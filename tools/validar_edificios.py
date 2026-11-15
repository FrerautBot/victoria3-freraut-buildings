#!/usr/bin/env python3
"""Validador estatico del sistema de edificios (M777, orden-67, task-70).

Reglas (6 checks + guard anti-vacuidad que cuenta, L310):
  1. building_sovereign_palace tiene possible con is_capital = yes
     (A490b: 1 palacio por pais, solo en la capital; V3 tiene UNA instancia
     del building por estado, los niveles no duplican).
  2. pm_sovereign_palace_base tiene state_modifiers con la clave de
     throughput elegida en P2 (building_sovereign_palace_throughput_add =
     0.10, precedente vanilla common/production_methods/08_monuments.txt:280
     building_government_administration_throughput_add = 0.2 en
     workforce_scaled), y esa clave NO esta en country_modifiers del mismo
     PM (B.2 check negativo) ni en otro PM (conteo total == 1).
     INPUTS OMITIDOS (P2): vanilla no ofrece clave por-building ni por
     building_group para inputs de bienes; solo existe
     building_goods_input_mult generico (01_building_modifier_types.txt:718)
     que en scope de estado afectaria a TODOS los edificios del estado.
     Fallback autorizado del briefing: omitir esa mitad y escalar a Lucas.
  3. Urbanizacion del palacio (A490b +40/nivel): el building group
     bg_sovereign_palace tiene urbanization = 40 (mecanismo vanilla
     primario, 00_building_groups.txt:18; doctrina M687 del repo: el PM
     NO debe usar state_urbanization_per_level_add — check negativo
     incluido). Desviacion documentada: common/building_groups/ estaba
     fuera de la lista autorizada del briefing pero el check de
     validar_minas.py (M687) lo impuso; reportado como hallazgo.
  4. Las 13 buildings activas del mod (lista cerrada, excluyendo
     public_health por decision de Lucas y excluyendo manufactura/trenes
     que el check 5 garantiza comentadas) tienen possible con
     is_incorporated = yes (A491). building_public_health NO debe tener
     is_incorporated (check negativo explicito).
  5. Partes D: los bloques building_manufacturing_center y
     building_industrial_trains estan comentados enteros (guardados en el
     archivo pero el juego no los carga): el header activo
     ^building_(manufacturing_center|industrial_trains)\\s*=\\s*\\{ no
     matchea ninguna linea y el header comentado
     ^#\\s*building_(manufacturing_center|industrial_trains) si matchea.
  6. Flats (B.0): pmg_sovereign_palace_flats existe en freraut_pmgs.txt,
     esta en production_method_groups de building_sovereign_palace, y
     pm_sovereign_palace_flats existe en freraut_pms.txt con los goods de
     B.0 (goods_input_furniture_add = 20, goods_input_groceries_add = 20,
     goods_output_services_add = 40).

Guard anti-vacuidad (M664 + L310): si los bloques esperados no se
encuentran, cada guard agrega una violacion al contador (el patron que
solo imprime esta prohibido aqui) y el exit code final lo refleja.

Exit code: 0 = sin violaciones, 1 = violaciones.
Uso:  python tools/validar_edificios.py [RAIZ]
      RAIZ opcional (M750): directorio con la estructura del mod
      (common/buildings/..., common/production_methods/...,
      common/production_method_groups/...); por defecto '.' (repo vigente).
"""
import os
import re
import sys

# M750: raiz opcional por argumento (fixtures del red test); default '.'
ROOT = sys.argv[1] if len(sys.argv) > 1 else "."
BASE = os.path.abspath(ROOT)

BUILDINGS_FILE = os.path.join(BASE, "common", "buildings",
                              "freraut_buildings.txt")
PMS_FILE = os.path.join(BASE, "common", "production_methods",
                        "freraut_pms.txt")
PMGS_FILE = os.path.join(BASE, "common", "production_method_groups",
                         "freraut_pmgs.txt")
BG_FILE = os.path.join(BASE, "common", "building_groups",
                       "freraut_building_groups.txt")

# 16 buildings del mod (anclas verificadas en Paso 0, HEAD del task)
TODAS_BUILDINGS = [
    "building_central_bank",
    "building_public_health",
    "building_mining_center",
    "building_manufacturing_center",
    "building_public_works",
    "building_sovereign_palace",
    "building_tech_university",
    "building_national_trade",
    "building_logistics_center",
    "building_national_academy",
    "building_stock_exchange",
    "building_dissident_agency",
    "building_fertilization_center",
    "building_industrial_trains",
    "building_breeding_center",
    "building_grand_company_bank",
]

# Check 4 (A491): edificios activos que deben exigir estado incorporado.
# Excluye public_health (decision de Lucas) y las 2 desactivadas del
# check 5 (manufactura/trenes, comentadas enteras por la Parte D).
INCORPORADAS = [
    "building_central_bank",
    "building_mining_center",
    "building_public_works",
    "building_sovereign_palace",
    "building_tech_university",
    "building_national_trade",
    "building_logistics_center",
    "building_national_academy",
    "building_stock_exchange",
    "building_dissident_agency",
    "building_fertilization_center",
    "building_breeding_center",
    "building_grand_company_bank",
]

# Bloques raiz activos esperados (16 - manufactura - trenes comentadas)
ACTIVAS_ESPERADAS = [b for b in TODAS_BUILDINGS
                     if b not in ("building_manufacturing_center",
                                  "building_industrial_trains")]

# Clave de throughput elegida en P2 (A490a +10%; percent semantics:
# building_throughput_add es percent=yes, 01_building_modifier_types.txt:730)
THROUGHPUT_KEY = "building_sovereign_palace_throughput_add"
THROUGHPUT_RE = re.compile(r"building_sovereign_palace_throughput_add"
                           r"\s*=\s*0\.10\b")
# Urbanizacion A490b: +40 por nivel via el campo urbanization del building
# group (mecanismo vanilla primario, 00_building_groups.txt:18; doctrina
# M687 del repo: state_urbanization_per_level_add en common/ es violacion)
URBANIZATION_RE = re.compile(r"urbanization\s*=\s*40\b")
URBANIZATION_PM_RE = re.compile(r"state_urbanization_per_level_add")
# P1/P4 triggers
IS_CAPITAL_RE = re.compile(r"is_capital\s*=\s*yes")
IS_INCORPORATED_RE = re.compile(r"is_incorporated\s*=\s*yes")
# Check 5: headers activos/comentados de los bloques desactivados
HEADER_ACTIVO_RE = re.compile(
    r"^building_(manufacturing_center|industrial_trains)\s*=\s*\{\s*$")
HEADER_COMENTADO_RE = re.compile(
    r"^#\s*building_(manufacturing_center|industrial_trains)\s*=\s*\{\s*$")
# Check 6: goods del PM de flats (B.0)
FLATS_FURNITURE_RE = re.compile(r"goods_input_furniture_add\s*=\s*20\b")
FLATS_GROCERIES_RE = re.compile(r"goods_input_groceries_add\s*=\s*20\b")
FLATS_SERVICES_RE = re.compile(r"goods_output_services_add\s*=\s*40\b")

BLOCK_HEADER_RE = re.compile(r"^(\S[\S ]*?)\s*=\s*\{\s*$")


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


def chequear_guard_buildings(violaciones, dict_buildings):
    """Anti-vacuidad: los 14 bloques activos esperados deben existir."""
    faltantes = [b for b in ACTIVAS_ESPERADAS if b not in dict_buildings]
    if faltantes:
        violaciones.append(
            ("freraut_buildings.txt",
             "GUARD anti-vacuidad: bloques activos no encontrados: %s"
             % ", ".join(faltantes)))
    else:
        print("[OK] guard anti-vacuidad: %d bloques activos presentes"
              % len(ACTIVAS_ESPERADAS))


def chequear_1_palacio_capital(violaciones, dict_buildings):
    bloque = dict_buildings.get("building_sovereign_palace")
    if bloque is None:
        violaciones.append(
            ("freraut_buildings.txt",
             "GUARD anti-vacuidad: building_sovereign_palace no encontrado"))
        return
    possible = sub_bloque_texto(bloque, "possible")
    if possible is None:
        violaciones.append(
            ("freraut_buildings.txt building_sovereign_palace",
             "check 1 (A490b): falta bloque possible (is_capital = yes "
             "exigido: 1 palacio por pais, solo en la capital)"))
    elif IS_CAPITAL_RE.search(possible):
        print("[OK] check 1 palacio possible con is_capital = yes "
              "(solo la capital; 1 instancia por estado = 1 palacio/pais)")
    else:
        violaciones.append(
            ("freraut_buildings.txt building_sovereign_palace",
             "check 1 (A490b): possible sin is_capital = yes"))


def chequear_2_throughput(violaciones, texto_pms):
    bloque = sub_bloque_texto(texto_pms, "pm_sovereign_palace_base")
    if bloque is None:
        violaciones.append(
            ("freraut_pms.txt",
             "GUARD anti-vacuidad: pm_sovereign_palace_base no encontrado"))
        return
    state_mods = sub_bloque_texto(bloque, "state_modifiers")
    if state_mods is None:
        violaciones.append(
            ("freraut_pms.txt pm_sovereign_palace_base",
             "check 2 (A490a): falta state_modifiers con "
             "building_sovereign_palace_throughput_add = 0.10 (+10% "
             "throughput solo del palacio en el estado de la capital)"))
    elif THROUGHPUT_RE.search(state_mods):
        print("[OK] check 2 throughput 0.10 en state_modifiers del palacio "
              "(precedente vanilla 08_monuments.txt:280)")
    else:
        violaciones.append(
            ("freraut_pms.txt pm_sovereign_palace_base",
             "check 2 (A490a): state_modifiers sin "
             "building_sovereign_palace_throughput_add = 0.10"))
    # B.2 check negativo: la clave no debe estar en country_modifiers
    country = sub_bloque_texto(bloque, "country_modifiers")
    if country and THROUGHPUT_KEY in country:
        violaciones.append(
            ("freraut_pms.txt pm_sovereign_palace_base",
             "check 2 (B.2): %s en country_modifiers (efecto de estado "
             "solo, no de pais)" % THROUGHPUT_KEY))
    # B.2: conteo total == 1 (no en otro PM)
    total = texto_pms.count(THROUGHPUT_KEY)
    if total == 1:
        print("[OK] check 2 (B.2) %s aparece 1 sola vez (ni en "
              "country_modifiers ni en otro PM)" % THROUGHPUT_KEY)
    else:
        violaciones.append(
            ("freraut_pms.txt",
             "check 2 (B.2): %s aparece %d veces (esperado 1)"
             % (THROUGHPUT_KEY, total)))
    print("[INFO] check 2 inputs -10% OMITIDO por P2: vanilla no ofrece "
          "clave por-building ni por building_group para inputs de bienes "
          "(solo building_goods_input_mult generico, que en scope de "
          "estado afectaria a todos los edificios). Fallback autorizado "
          "del briefing: omitir y escalar a Lucas.")


def chequear_3_urbanizacion(violaciones, texto_pms):
    if not os.path.isfile(BG_FILE):
        violaciones.append(
            ("freraut_building_groups.txt",
             "GUARD anti-vacuidad: archivo de building groups no encontrado "
             "(%s)" % BG_FILE))
        return
    bg_texto = "\n".join(leer(BG_FILE))
    bg_palacio = sub_bloque_texto(bg_texto, "bg_sovereign_palace")
    if bg_palacio is None:
        violaciones.append(
            ("freraut_building_groups.txt",
             "GUARD anti-vacuidad: bg_sovereign_palace no encontrado"))
        return
    if URBANIZATION_RE.search(bg_palacio):
        print("[OK] check 3 urbanizacion +40 por nivel del palacio "
              "(campo urbanization del building group, mecanismo vanilla "
              "primario 00_building_groups.txt:18; doctrina M687 del repo)")
    else:
        violaciones.append(
            ("freraut_building_groups.txt bg_sovereign_palace",
             "check 3 (A490b): urbanization != 40 (se exige +40 por nivel "
             "del palacio via el campo urbanization del building group)"))
    # M687 check negativo: la clave per-level de estado NO debe usarse en
    # common/ del mod (validar_minas.py ya lo exige a nivel repo; aqui
    # queda cubierto dentro del alcance de este validador)
    if URBANIZATION_PM_RE.search(texto_pms):
        violaciones.append(
            ("freraut_pms.txt",
             "check 3 (M687): state_urbanization_per_level_add presente en "
             "freraut_pms.txt (no usar; la urbanizacion per-level es el "
             "campo urbanization del building group)"))
    else:
        print("[OK] check 3 (M687) sin state_urbanization_per_level_add "
              "en freraut_pms.txt")


def chequear_4_incorporadas(violaciones, dict_buildings):
    for key in INCORPORADAS:
        bloque = dict_buildings.get(key)
        if bloque is None:
            violaciones.append(
                ("freraut_buildings.txt",
                 "GUARD anti-vacuidad: %s no encontrado" % key))
            continue
        possible = sub_bloque_texto(bloque, "possible")
        if possible is None:
            violaciones.append(
                ("freraut_buildings.txt %s" % key,
                 "check 4 (A491): falta possible con is_incorporated = yes "
                 "(no construible en colonias/territorios)"))
        elif IS_INCORPORATED_RE.search(possible):
            print("[OK] check 4 %s possible con is_incorporated = yes" % key)
        else:
            violaciones.append(
                ("freraut_buildings.txt %s" % key,
                 "check 4 (A491): possible sin is_incorporated = yes"))
    # Check negativo: public_health exenta por decision de Lucas
    salud = dict_buildings.get("building_public_health")
    if salud is None:
        violaciones.append(
            ("freraut_buildings.txt",
             "GUARD anti-vacuidad: building_public_health no encontrado"))
    elif IS_INCORPORATED_RE.search(salud):
        violaciones.append(
            ("freraut_buildings.txt building_public_health",
             "check 4 negativo: public_health tiene is_incorporated "
             "(Lucas la exenta de A491)"))
    else:
        print("[OK] check 4 negativo: public_health sin is_incorporated "
              "(exenta por decision de Lucas)")


def chequear_5_desactivadas(violaciones):
    lineas = leer(BUILDINGS_FILE)
    activos = [n for n, l in enumerate(lineas, 1)
               if HEADER_ACTIVO_RE.match(l.strip())]
    comentados = [n for n, l in enumerate(lineas, 1)
                  if HEADER_COMENTADO_RE.match(l.strip())]
    if activos:
        violaciones.append(
            ("freraut_buildings.txt",
             "check 5 (Parte D): headers activos de manufactura/trenes en "
             "lineas %s (deben estar comentados: guardados en el archivo "
             "pero el juego no los carga)" % activos))
    else:
        print("[OK] check 5 manufactura/trenes sin headers activos")
    esperados = {"building_manufacturing_center": False,
                 "building_industrial_trains": False}
    for n in comentados:
        for key in esperados:
            if key in lineas[n - 1]:
                esperados[key] = True
    faltan = [k for k, v in esperados.items() if not v]
    if faltan:
        violaciones.append(
            ("freraut_buildings.txt",
             "check 5 (Parte D): bloques no encontrados comentados: %s"
             % ", ".join(faltan)))
    else:
        print("[OK] check 5 bloques de manufactura y trenes comentados "
              "enteros (guardados, no cargan)")


def chequear_6_flats(violaciones, texto_pmgs, dict_buildings, texto_pms):
    raices_pmgs = {nombre: texto for nombre, texto in bloques_raiz(PMGS_FILE)}
    if "pmg_sovereign_palace_flats" not in raices_pmgs:
        violaciones.append(
            ("freraut_pmgs.txt",
             "check 6 (B.0): pmg_sovereign_palace_flats no existe"))
    else:
        print("[OK] check 6 pmg_sovereign_palace_flats definido")
    palacio = dict_buildings.get("building_sovereign_palace")
    if palacio is None:
        violaciones.append(
            ("freraut_buildings.txt",
             "GUARD anti-vacuidad: building_sovereign_palace no encontrado"))
    elif "pmg_sovereign_palace_flats" in palacio:
        print("[OK] check 6 palacio con pmg_sovereign_palace_flats en "
              "production_method_groups")
    else:
        violaciones.append(
            ("freraut_buildings.txt building_sovereign_palace",
             "check 6 (B.0): production_method_groups sin "
             "pmg_sovereign_palace_flats"))
    pm_flats = sub_bloque_texto(texto_pms, "pm_sovereign_palace_flats")
    if pm_flats is None:
        violaciones.append(
            ("freraut_pms.txt",
             "check 6 (B.0): pm_sovereign_palace_flats no existe"))
        return
    for regex, bien in ((FLATS_FURNITURE_RE, "furniture 20"),
                        (FLATS_GROCERIES_RE, "groceries 20"),
                        (FLATS_SERVICES_RE, "services 40")):
        if regex.search(pm_flats):
            print("[OK] check 6 flats goods %s" % bien)
        else:
            violaciones.append(
                ("freraut_pms.txt pm_sovereign_palace_flats",
                 "check 6 (B.0): falta %s" % bien))


def main():
    violaciones = []
    dict_buildings = {nombre: texto
                      for nombre, texto in bloques_raiz(BUILDINGS_FILE)}
    texto_pms = "\n".join(leer(PMS_FILE))
    texto_pmgs = "\n".join(leer(PMGS_FILE))

    chequear_guard_buildings(violaciones, dict_buildings)
    chequear_1_palacio_capital(violaciones, dict_buildings)
    chequear_2_throughput(violaciones, texto_pms)
    chequear_3_urbanizacion(violaciones, texto_pms)
    chequear_4_incorporadas(violaciones, dict_buildings)
    chequear_5_desactivadas(violaciones)
    chequear_6_flats(violaciones, texto_pmgs, dict_buildings, texto_pms)

    for etiqueta, mensaje in violaciones:
        print("VIOLACION %s: %s" % (etiqueta, mensaje))
    print("violaciones: %d" % len(violaciones))
    return 1 if violaciones else 0


if __name__ == "__main__":
    sys.exit(main())
