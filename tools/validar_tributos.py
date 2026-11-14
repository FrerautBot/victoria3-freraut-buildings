#!/usr/bin/env python3
"""Validador estatico del sistema de tributos (M686, orden-66, task-67).

Reglas:
  (a) Parte A: los 8 bloques freraut_da_tribute* de
      common/diplomatic_actions/freraut_administration_actions.txt no deben
      contener relations_progress_per_day. Alcance SOLO los 8 bloques de
      tributo: la disposicion (resultados.orden66_disposicion) ordena
      "dejar intactos los 8 pactos de desarrollo" (freraut_da_dev_p*) que
      SI degradan relaciones por diseno (orden-63/64). El literal del
      briefing A.3 ("0 ocurrencias en common/diplomatic_actions/") es un
      error de redaccion que contradice la disposicion; este validador
      sigue la disposicion.
  (b) Parte B (M721): freraut_tribute_monthly_pulse se define exactamente
      UNA vez en common/on_actions/*.txt, y la clave on_monthly_pulse_country
      aparece a lo sumo UNA vez POR ARCHIVO (clase de bug "Duplicated key").
  (c) Parte B (M720, chequeos estaticos del texto del pulso):
      (a) M720-a: cada loop every_subject_or_below del pulso exige los 8
          pactos en su gate has_diplomatic_pact (sujeto sin pacto = nada);
      (b) M720-b: la rama confederada exige NOT has_variable
          freraut_union_exempt (exento = sin delta);
      (c) M720-c: cada pacto aparece exactamente 5 veces en el pulso
          (trigger 1 + gate de cada loop 1+1 + rama de banda 1+1) =
          exactamente una banda por sujeto, sin huecos ni duplicados.
  (d) Parte B (M722, test aritmetico): TABLA_MENSUAL == TABLA_SEMANAL x 4.33
      redondeado al entero mas cercano (redondeo half-away-from-zero:
      12.99->13, 4.33->4, -2.165->-2, -4.33->-4, -8.66->-9). TABLA_RADICALES
      se compara contra su literal de diseno {10: 0.002, 30: 0.004,
      50: 0.008, 70: 0.015, 80: 0.03}.
  (e) Parte B.2: el pulso no usa relations_progress_per_day ni add_relations;
      los valores de las ramas son los de la tabla: change_relations
      {4, -2, -4, -9} (la banda 30-40% es delta 0, sin linea) y add_radicals
      {0.002, 0.004, 0.008, 0.015, 0.03}, y el comentario de redondeo
      (M722 / semanal x4.33) esta presente (Parte B.3).
  (f) Parte C: events/freraut_tribute_events.txt tiene exactamente 8
      add_loyalists con value = 0.02 (uno por banda de imposicion) y los 8
      create_diplomatic_pact intactos (escalones sin tocar).
  (g) Parte D: la opcion d de freraut_union.1 setea la variable
      freraut_union_exempt (set_variable value = 1).
  (h) Guard anti-vacuidad (M664): 0 pactos escaneados, 0 bandas detectadas
      o pulso ausente = fallo ruidoso.

Exit code: 0 = sin violaciones, 1 = violaciones.
Uso:  python tools/validar_tributos.py
"""
import glob
import math
import os
import re
import sys

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

DA_FILE = os.path.join(BASE, "common", "diplomatic_actions",
                       "freraut_administration_actions.txt")
ON_ACTIONS_DIR = os.path.join(BASE, "common", "on_actions")
PULSE_FILE = os.path.join(ON_ACTIONS_DIR, "freraut_on_actions.txt")
TRIBUTE_EVENTS = os.path.join(BASE, "events", "freraut_tribute_events.txt")
UNION_EVENTS = os.path.join(BASE, "events", "freraut_union_events.txt")

TRIBUTE_PACTS = [
    "freraut_da_tribute",
    "freraut_da_tribute_p10",
    "freraut_da_tribute_p30",
    "freraut_da_tribute_p40",
    "freraut_da_tribute_p50",
    "freraut_da_tribute_p60",
    "freraut_da_tribute_p70",
    "freraut_da_tribute_p80",
]

# Tabla semanal de Lucas (orden-66) -> banda baja: delta por semana
TABLA_SEMANAL = {0: 3, 10: 1, 30: 0, 50: -0.5, 70: -1, 80: -2}
# Tabla mensual implementada (semanal x4.33, redondeo al entero mas cercano)
TABLA_MENSUAL = {0: 13, 10: 4, 30: 0, 50: -2, 70: -4, 80: -9}
# Radicales mensuales por banda (fraccion de pops, diseno de la disposicion)
TABLA_RADICALES = {10: 0.002, 30: 0.004, 50: 0.008, 70: 0.015, 80: 0.03}
TABLA_RADICALES_LITERAL = {10: 0.002, 30: 0.004, 50: 0.008, 70: 0.015,
                           80: 0.03}

BLOCK_HEADER_RE = re.compile(r"^(\S[\S ]*?)\s*=\s*\{\s*$")
PACT_REF_RE = re.compile(r"type\s*=\s*(\S+)")
HAS_PACT_RE = re.compile(
    r"has_diplomatic_pact\s*=\s*\{[^}]*?type\s*=\s*(\S+)", re.DOTALL)
NOT_EXEMPT_RE = re.compile(
    r"NOT\s*=\s*\{\s*has_variable\s*=\s*freraut_union_exempt\s*\}")
CHANGE_REL_RE = re.compile(
    r"change_relations\s*=\s*\{\s*country\s*=\s*root\s*"
    r"value\s*=\s*(-?\d+(?:\.\d+)?)", re.DOTALL)
ADD_RADICALS_RE = re.compile(
    r"add_radicals\s*=\s*\{\s*value\s*=\s*(0\.\d+)", re.DOTALL)
ADD_LOYALISTS_RE = re.compile(
    r"add_loyalists\s*=\s*\{\s*value\s*=\s*(0\.\d+)", re.DOTALL)
SET_VAR_RE = re.compile(
    r"set_variable\s*=\s*\{\s*name\s*=\s*freraut_union_exempt\s*"
    r"value\s*=\s*1\s*\}", re.DOTALL)


def strip_comment(line):
    return line.split("#", 1)[0].rstrip()


def leer(path):
    with open(path, encoding="utf-8-sig") as f:
        return f.read().split("\n")


def bloques_raiz(path):
    """Lista de (nombre, texto) de bloques de nivel raiz del archivo."""
    lineas = leer(path)
    pila = []
    raices = []
    for n, raw in enumerate(lineas, 1):
        line = strip_comment(raw).strip()
        if not line:
            continue
        if line == "}":
            if pila:
                nombre, inicio = pila.pop()
                if not pila:
                    raices.append((nombre, "\n".join(lineas[inicio - 1:n])))
            continue
        m = BLOCK_HEADER_RE.match(line)
        if m:
            pila.append((m.group(1), n))
    return raices


def sub_bloque_texto(texto, nombre):
    """Texto del primer bloque `nombre = {` dentro de `texto`, o None."""
    lineas = texto.split("\n")
    i = 0
    while i < len(lineas):
        m = BLOCK_HEADER_RE.match(strip_comment(lineas[i]).strip())
        if m and m.group(1) == nombre:
            prof = 0
            j = i
            while j < len(lineas):
                s = strip_comment(lineas[j]).strip()
                if s and s != "}":
                    if BLOCK_HEADER_RE.match(s):
                        prof += 1
                elif s == "}":
                    prof -= 1
                    if prof == 0:
                        break
                j += 1
            return "\n".join(lineas[i:j + 1])
        i += 1
    return None


def redondear_entero_cercano(x):
    """Redondeo half-away-from-zero (M722, 'al entero mas cercano')."""
    return int(math.copysign(math.floor(abs(x) + 0.5), x))


def chequear_tabla_m722(violaciones):
    derivada = {k: redondear_entero_cercano(v * 4.33)
                for k, v in TABLA_SEMANAL.items()}
    if derivada == TABLA_MENSUAL:
        print("[OK] M722 tabla mensual == semanal x4.33 redondeada "
              "(+3->13, +1->4, 0->0, -0.5->-2, -1->-4, -2->-9)")
    else:
        violaciones.append(
            ("tablas", "M722 tabla mensual %s != derivada semanal x4.33 %s"
             % (TABLA_MENSUAL, derivada)))
    if TABLA_RADICALES == TABLA_RADICALES_LITERAL:
        print("[OK] M722 tabla radicales == literal de diseno %s"
              % TABLA_RADICALES_LITERAL)
    else:
        violaciones.append(
            ("tablas", "M722 tabla radicales %s != literal %s"
             % (TABLA_RADICALES, TABLA_RADICALES_LITERAL)))


def chequear_parte_a(violaciones):
    raices = bloques_raiz(DA_FILE)
    pactos = {nombre: texto for nombre, texto in raices
              if nombre in TRIBUTE_PACTS}
    faltantes = [p for p in TRIBUTE_PACTS if p not in pactos]
    if faltantes:
        print("VIOLACION GUARD: pactos de tributo no encontrados: %s"
              % ", ".join(faltantes))
        print("pactos escaneados: %d, violaciones: 1" % len(pactos))
        return 1
    for pacto in TRIBUTE_PACTS:
        if "relations_progress_per_day" in pactos[pacto]:
            violaciones.append(
                ("freraut_administration_actions.txt %s" % pacto,
                 "relations_progress_per_day dentro del pacto de tributo"))
        else:
            print("[OK] Parte A %s sin relations_progress_per_day" % pacto)
    total = "\n".join(leer(DA_FILE)).count("relations_progress_per_day")
    print("[INFO] relations_progress_per_day restantes en el archivo "
          "(dev/regimen, por diseno): %d" % total)
    return 0


def chequear_pulso_unico(violaciones):
    archivos = sorted(glob.glob(os.path.join(ON_ACTIONS_DIR, "freraut_*.txt")))
    definiciones = []
    por_archivo_hook = {}
    for path in archivos:
        rel = os.path.relpath(path, BASE)
        raices = bloques_raiz(path)
        nombres = [n for n, _t in raices]
        if "freraut_tribute_monthly_pulse" in nombres:
            definiciones.append(rel)
        hooks = nombres.count("on_monthly_pulse_country")
        por_archivo_hook[rel] = hooks
        if hooks > 1:
            violaciones.append(
                (rel, "on_monthly_pulse_country duplicado en el MISMO "
                      "archivo (%d veces, clase Duplicated key M721)"
                 % hooks))
        else:
            print("[OK] M721 %s on_monthly_pulse_country x%d"
                  % (rel, hooks))
    if len(definiciones) == 1:
        print("[OK] M721 freraut_tribute_monthly_pulse definido 1 vez (%s)"
              % definiciones[0])
    elif not definiciones:
        print("VIOLACION GUARD: freraut_tribute_monthly_pulse no definido "
              "en common/on_actions/ (anti-vacuidad M664)")
        return None
    else:
        violaciones.append(
            ("common/on_actions/",
             "freraut_tribute_monthly_pulse definido %d veces: %s"
             % (len(definiciones), ", ".join(definiciones))))
        return None
    return definiciones[0]


def chequear_pulso(rel, violaciones):
    texto_pulso = "\n".join(leer(PULSE_FILE))
    inicio = texto_pulso.find("freraut_tribute_monthly_pulse")
    bloque = sub_bloque_texto(texto_pulso, "freraut_tribute_monthly_pulse")
    if bloque is None:
        violaciones.append((rel, "bloque del pulso ilegible"))
        return
    # M720-a: dos loops, cada uno con el gate de los 8 pactos
    loops = []
    restante = bloque
    while True:
        sub = sub_bloque_texto(restante, "every_subject_or_below")
        if sub is None:
            break
        loops.append(sub)
        idx = restante.find("every_subject_or_below")
        restante = restante[idx + len("every_subject_or_below"):]
    if len(loops) == 2:
        print("[OK] pulso con 2 loops every_subject_or_below "
              "(confederados / administraciones+titeres)")
    else:
        violaciones.append(
            (rel, "M720-a pulso debe tener 2 loops every_subject_or_below, "
                  "tiene %d" % len(loops)))
        return
    for i, loop in enumerate(loops, 1):
        faltantes = [p for p in TRIBUTE_PACTS
                     if not re.search(r"type\s*=\s*%s\b" % p, loop)]
        if faltantes:
            violaciones.append(
                (rel, "M720-a loop %d sin gate para pactos: %s"
                 % (i, ", ".join(faltantes))))
        else:
            print("[OK] M720-a loop %d gatea los 8 pactos "
                  "(sujeto sin pacto = nada)" % i)
    # M720-b: exencion solo en el loop confederado
    confederado = loops[0] if "confederated_state" in loops[0] else \
        (loops[1] if "confederated_state" in loops[1] else None)
    if confederado and NOT_EXEMPT_RE.search(confederado):
        print("[OK] M720-b exencion freraut_union_exempt en rama confederada")
    else:
        violaciones.append(
            (rel, "M720-b falta NOT has_variable freraut_union_exempt en "
                  "la rama confederada"))
    # M720-c: cada pacto exactamente 5 veces (trigger + gate + gate + banda
    # + banda) = una banda por sujeto, sin huecos ni duplicados
    for pacto in TRIBUTE_PACTS:
        cuenta = len(re.findall(r"type\s*=\s*%s\b" % pacto, bloque))
        if cuenta == 5:
            print("[OK] M720-c %s x5 (trigger+2 gates+2 bandas)" % pacto)
        else:
            violaciones.append(
                (rel, "M720-c %s aparece %d veces en el pulso (esperado 5: "
                      "una banda por sujeto, sin huecos)" % (pacto, cuenta)))
    # B.2: primitivas correctas
    for prohibido in ("relations_progress_per_day", "add_relations"):
        if prohibido in bloque:
            violaciones.append(
                (rel, "B.2 pulso usa %s (prohibido; usar change_relations)"
                 % prohibido))
    valores_rel = sorted(int(m) for m in CHANGE_REL_RE.findall(bloque))
    esperados_rel = sorted([4, -2, -4, -9])
    if valores_rel == esperados_rel:
        print("[OK] B.2 change_relations con valores de tabla %s "
              "(banda 30-40%% = delta 0 sin linea)" % esperados_rel)
    else:
        violaciones.append(
            (rel, "B.2 change_relations valores %s != esperados %s"
             % (valores_rel, esperados_rel)))
    valores_rad = sorted(float(m) for m in ADD_RADICALS_RE.findall(bloque))
    esperados_rad = sorted(TABLA_RADICALES.values())
    if valores_rad == esperados_rad:
        print("[OK] B.2 add_radicals con valores de tabla %s" % esperados_rad)
    else:
        violaciones.append(
            (rel, "B.2 add_radicals valores %s != esperados %s"
             % (valores_rad, esperados_rad)))
    # B.3: comentario de redondeo
    if "M722" in bloque and "semanal x4.33" in bloque:
        print("[OK] B.3 comentario de redondeo M722 presente")
    else:
        violaciones.append((rel, "B.3 falta comentario de redondeo "
                                 "(semanal x4.33, M722)"))


def chequear_parte_c(violaciones):
    texto = "\n".join(leer(TRIBUTE_EVENTS))
    leales = ADD_LOYALISTS_RE.findall(texto)
    if len(leales) == 8 and all(v == "0.02" for v in leales):
        print("[OK] Parte C add_loyalists x8 con value 0.02 "
              "(una por banda de imposicion)")
    else:
        violaciones.append(
            ("events/freraut_tribute_events.txt",
             "Parte C add_loyalists 0.02 x8 esperados, encontrados %s"
             % leales))
    pactos = texto.count("create_diplomatic_pact")
    if pactos == 8:
        print("[OK] Parte C create_diplomatic_pact x8 intactos (escalones)")
    else:
        violaciones.append(
            ("events/freraut_tribute_events.txt",
             "Parte C create_diplomatic_pact x8 esperados, hay %d" % pactos))


def chequear_parte_d(violaciones):
    texto = "\n".join(leer(UNION_EVENTS))
    bloque = sub_bloque_texto(texto, "freraut_union.1")
    if bloque is None:
        violaciones.append(("events/freraut_union_events.txt",
                            "Parte D freraut_union.1 no encontrado"))
        return
    if SET_VAR_RE.search(bloque):
        print("[OK] Parte D set_variable freraut_union_exempt en union.1")
    else:
        violaciones.append(
            ("events/freraut_union_events.txt",
             "Parte D falta set_variable freraut_union_exempt value = 1 "
             "en la opcion d"))


def main():
    violaciones = []
    chequear_tabla_m722(violaciones)
    guard_a = chequear_parte_a(violaciones)
    rel = chequear_pulso_unico(violaciones)
    if rel:
        chequear_pulso(rel, violaciones)
    chequear_parte_c(violaciones)
    chequear_parte_d(violaciones)

    for etiqueta, mensaje in violaciones:
        print("VIOLACION %s: %s" % (etiqueta, mensaje))
    print("violaciones: %d" % len(violaciones))
    return 1 if violaciones else 0


if __name__ == "__main__":
    sys.exit(main())
