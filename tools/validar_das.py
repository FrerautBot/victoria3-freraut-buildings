#!/usr/bin/env python3
"""Validador estatico de acciones diplomaticas (DAs) del mod (M666, task-66).

Reglas:
  (a) cada bloque DA de nivel raiz en common/diplomatic_actions/freraut_*.txt
      debe tener potential, possible y (accept_effect | effect);
  (b) scope:target_country debe aparecer en potential y en possible
      (patron de gate del mod; exencion documentada: possible vacuo
      `always = yes`, diseno deliberado de da_freraut_implement_regime y
      freraut_da_union_tribute);
  (c) cada trigger_event = { id = X } debe referenciar un X = { definido en
      events/*.txt;
  (d) cada uso de scope:X dentro de accept_effect/effect debe tener su
      save_scope_as = X | save_temporary_scope_as = X ANTES (mismo bloque,
      orden de linea); scope:target_country/actor/recipient son built-ins;
  (e) anti-clase-de-bug orden-65: si hay show_as_tooltip y 0 lineas de
      efecto real FUERA de el (excluyendo custom_tooltip/show_as_tooltip/
      custom_description), el efecto no se ejecuta -> violacion grave;
  (f) claves de localizacion: para cada bloque DA freraut_da_X se exige en
      espanol e ingles (union de los dos YML de cada idioma):
      freraut_da_X, freraut_da_X_desc y, si should_notify_third_parties=yes,
      freraut_da_X_action_notification_name/_desc. Las claves
      _action_notification_third_party_name/_desc se exigen all-or-nothing:
      media pareja = violacion; pareja ausente = aviso (5 DAs de orden-54/56
      la omiten: exigirla romperia el cierre "0 violaciones" de este task;
      queda registrado como hallazgo para follow-up).
  (g) guard anti-vacuidad: 0 bloques DA escaneados = fallo ruidoso.

Los bloques con `pact = {` hijo directo son DEFINICIONES DE PACTO, no DAs:
se omiten de los chequeos (se informa el conteo).

Exit code: 0 = sin violaciones, 1 = violaciones.
Uso:  python tools/validar_das.py
"""
import glob
import os
import re
import sys

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

DA_DIR = os.path.join(BASE, "common", "diplomatic_actions")
EVENTS_DIR = os.path.join(BASE, "events")
LOC_FILES = {
    "spanish": [
        os.path.join("localization", "spanish",
                     "freraut_confederate_l_spanish.yml"),
        os.path.join("localization", "spanish",
                     "freraut_buildings_l_spanish.yml"),
    ],
    "english": [
        os.path.join("localization", "english",
                     "freraut_confederate_l_english.yml"),
        os.path.join("localization", "english",
                     "freraut_buildings_l_english.yml"),
    ],
}

BUILTIN_SCOPES = {"target_country", "actor", "recipient",
                  "secondary_recipient"}

BLOCK_HEADER_RE = re.compile(r"^(\S[\S ]*?)\s*=\s*\{\s*$")
SAVE_SCOPE_RE = re.compile(
    r"(?:save_scope_as|save_temporary_scope_as)\s*=\s*(\S+)")
SCOPE_USE_RE = re.compile(r"scope:(\w+)")
TRIGGER_EVENT_RE = re.compile(
    r"trigger_event\s*=\s*\{[^}]*?\bid\s*=\s*([A-Za-z0-9_.]+)", re.DOTALL)
LOC_KEY_RE = re.compile(r"^\s*(\S+):")
EXCLUDED_WRAPPERS = {"show_as_tooltip", "custom_tooltip",
                     "custom_description"}


def strip_comment(line):
    return line.split("#", 1)[0].rstrip()


def leer(path):
    with open(path, encoding="utf-8-sig") as f:
        return f.read().split("\n")


def bloques_con_anidamiento(path):
    """Devuelve (raices, hijos_por_raiz) para el archivo `path`.

    raices: lista de (nombre, linea_inicio, linea_fin) de bloques de nivel
    raiz. hijos_por_raiz: dict nombre -> set de nombres de bloques que son
    hijos directos (profundidad 1) de esa raiz. Lineas 1-based, rango
    [inicio, fin] inclusivo de llaves."""
    lineas = leer(path)
    pila = []
    raices = []
    hijos = {}
    for n, raw in enumerate(lineas, 1):
        line = strip_comment(raw).strip()
        if not line:
            continue
        if line == "}":
            if pila:
                nombre, inicio, _prof = pila.pop()
                if len(pila) == 1:
                    hijos.setdefault(pila[0][0], set()).add(nombre)
                if not pila:
                    raices.append((nombre, inicio, n))
            continue
        m = BLOCK_HEADER_RE.match(line)
        if m:
            pila.append((m.group(1), n, len(pila)))
    return raices, hijos


def bloques_da():
    """Escanea los DA del mod. Devuelve (das, pactos, errores).

    das: lista de (nombre, path, linea, texto, hijos) para bloques raiz sin
    hijo directo `pact = {`. pactos: lista de nombres omitidos. errores:
    lista de strings de infraestructura (archivos faltantes)."""
    das, pactos, errores = [], [], []
    archivos = sorted(glob.glob(os.path.join(DA_DIR, "freraut_*.txt")))
    if not archivos:
        errores.append("GUARD: no hay freraut_*.txt en %s" % DA_DIR)
        return das, pactos, errores
    for path in archivos:
        rel = os.path.relpath(path, BASE)
        raices, hijos = bloques_con_anidamiento(path)
        lineas = leer(path)
        for nombre, inicio, fin in raices:
            if "pact" in hijos.get(nombre, set()):
                pactos.append(nombre)
                continue
            texto = "\n".join(lineas[inicio - 1:fin])
            das.append((nombre, rel, inicio, texto, hijos.get(nombre, set())))
    return das, pactos, errores


def linea_de(texto_bloque, aguja, linea_inicio):
    for i, linea in enumerate(texto_bloque.split("\n"), 1):
        if aguja in strip_comment(linea):
            return linea_inicio + i - 1
    return linea_inicio


def sub_bloque(texto_bloque, nombre, linea_inicio):
    """Extrae (texto, linea_abs_inicio, lineas_con_numero) del primer bloque
    `nombre = {` dentro de texto_bloque, o None."""
    lineas = texto_bloque.split("\n")
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
            cuerpo = [(linea_inicio + k, lineas[k]) for k in range(i, j + 1)]
            return "\n".join(lineas[i:j + 1]), linea_inicio + i, cuerpo
        i += 1
    return None


def chequear_estructura(bloque, violaciones):
    nombre, rel, linea, texto, hijos = bloque
    etiqueta = "%s:%d %s" % (rel, linea, nombre)
    for requerido, mensaje in (("potential", "sin potential"),
                               ("possible", "sin possible")):
        if requerido not in hijos:
            violaciones.append((etiqueta, mensaje))
        else:
            print("[OK] %s %s" % (etiqueta, requerido))
    if "accept_effect" in hijos or "effect" in hijos:
        print("[OK] %s %s" % (etiqueta,
                              "accept_effect" if "accept_effect" in hijos
                              else "effect"))
    else:
        violaciones.append((etiqueta, "sin accept_effect ni effect"))


def es_possible_vacuo(cuerpo):
    lineas = [strip_comment(l).strip() for _n, l in cuerpo]
    lineas = [l for l in lineas if l and l != "}"]
    lineas = [l for l in lineas if not BLOCK_HEADER_RE.match(l)]
    return lineas == ["always = yes"]


def chequear_gate(bloque, violaciones):
    nombre, rel, linea, texto, hijos = bloque
    etiqueta = "%s:%d %s" % (rel, linea, nombre)
    sub = sub_bloque(texto, "potential", linea)
    if sub and "scope:target_country" in sub[0]:
        print("[OK] %s potential gate scope:target_country" % etiqueta)
    else:
        violaciones.append(
            (etiqueta, "potential sin scope:target_country"))
    sub = sub_bloque(texto, "possible", linea)
    if sub:
        if "scope:target_country" in sub[0]:
            print("[OK] %s possible gate scope:target_country" % etiqueta)
        elif es_possible_vacuo(sub[2]):
            print("[OK] %s possible vacuo (always = yes, diseno deliberado)"
                  % etiqueta)
        else:
            violaciones.append(
                (etiqueta, "possible sin scope:target_country"))


def chequear_trigger_event(bloque, eventos_definidos, violaciones):
    nombre, rel, linea, texto, hijos = bloque
    etiqueta = "%s:%d %s" % (rel, linea, nombre)
    encontrados = TRIGGER_EVENT_RE.findall(texto)
    for eid in encontrados:
        if eid not in eventos_definidos:
            violaciones.append(
                (etiqueta, "trigger_event id %s no definido en events/"
                 % eid))
        else:
            print("[OK] %s trigger_event %s definido en events/"
                  % (etiqueta, eid))
    if not encontrados:
        print("[OK] %s sin trigger_event" % etiqueta)


def chequear_save_scopes(bloque, violaciones):
    nombre, rel, linea, texto, hijos = bloque
    etiqueta = "%s:%d %s" % (rel, linea, nombre)
    efecto = None
    for candidato in ("accept_effect", "effect"):
        if candidato in hijos:
            efecto = sub_bloque(texto, candidato, linea)
            break
    if not efecto:
        return
    cuerpo = efecto[2]
    definiciones = {}
    for n_abs, raw in cuerpo:
        for m in SAVE_SCOPE_RE.finditer(strip_comment(raw)):
            definiciones.setdefault(m.group(1), []).append(n_abs)
    violado = False
    for n_abs, raw in cuerpo:
        for m in SCOPE_USE_RE.finditer(strip_comment(raw)):
            usado = m.group(1)
            if usado in BUILTIN_SCOPES:
                continue
            previas = [d for d in definiciones.get(usado, []) if d < n_abs]
            if not previas:
                violaciones.append(
                    ("%s:%d" % (rel, n_abs),
                     "scope:%s usado sin save_scope_as previo en %s"
                     % (usado, "accept_effect" if "accept_effect" in hijos
                        else "effect")))
                violado = True
    if not violado:
        print("[OK] %s save_scope_as ordenados (usos con definicion previa)"
              % etiqueta)


def contar_efectos_reales(cuerpo):
    """Cuenta lineas de efecto fuera de show_as_tooltip/custom_tooltip/
    custom_description. `cuerpo` incluye la llave de apertura del
    accept_effect/effect; se la excluye de la cuenta."""
    cuenta = 0
    pila = []
    for n_abs, raw in cuerpo:
        s = strip_comment(raw).strip()
        if not s or s == "}":
            if s == "}" and pila:
                pila.pop()
            continue
        m = BLOCK_HEADER_RE.match(s)
        if m:
            nombre_bloque = m.group(1)
            excluido = nombre_bloque in EXCLUDED_WRAPPERS
            if not excluido and not (not pila and nombre_bloque in
                                     ("accept_effect", "effect")):
                cuenta += 1
            pila.append(excluido)
            continue
        if pila and pila[-1]:
            continue
        cuenta += 1
    return cuenta


def chequear_show_as_tooltip(bloque, violaciones):
    nombre, rel, linea, texto, hijos = bloque
    etiqueta = "%s:%d %s" % (rel, linea, nombre)
    efecto = None
    for candidato in ("accept_effect", "effect"):
        if candidato in hijos:
            efecto = sub_bloque(texto, candidato, linea)
            break
    if not efecto:
        return
    cuerpo = efecto[2]
    if "show_as_tooltip" not in efecto[0]:
        print("[OK] %s sin show_as_tooltip en efecto" % etiqueta)
        return
    reales = contar_efectos_reales(cuerpo)
    if reales == 0:
        violaciones.append(
            ("%s:%d" % (rel, efecto[1]),
             "efecto solo dentro de show_as_tooltip (no se ejecuta)"))
    else:
        print("[OK] %s show_as_tooltip con %d efectos reales fuera"
              % (etiqueta, reales))


def cargar_loc():
    """Devuelve {idioma: set(claves)} con la union de los dos YML por
    idioma."""
    claves = {}
    for idioma, paths in LOC_FILES.items():
        todas = set()
        for p in paths:
            abs_p = os.path.join(BASE, p)
            if os.path.exists(abs_p):
                for linea in leer(abs_p):
                    m = LOC_KEY_RE.match(linea)
                    if m:
                        todas.add(m.group(1))
        claves[idioma] = todas
    return claves


def chequear_loc(bloque, loc, violaciones, avisos):
    nombre, rel, linea, texto, hijos = bloque
    if not nombre.startswith("freraut_da_"):
        print("[OK] %s:%d %s loc fuera de alcance (no es freraut_da_*)"
              % (rel, linea, nombre))
        return
    etiqueta = "%s:%d %s" % (rel, linea, nombre)
    notifica = "should_notify_third_parties = yes" in texto
    requeridas = [nombre, nombre + "_desc"]
    if notifica:
        requeridas += [nombre + "_action_notification_name",
                       nombre + "_action_notification_desc"]
    for clave in requeridas:
        for idioma in ("spanish", "english"):
            if clave in loc[idioma]:
                print("[OK] %s loc %s:%s" % (etiqueta, idioma, clave))
            else:
                violaciones.append(
                    (etiqueta, "loc %s falta clave %s" % (idioma, clave)))
    if notifica:
        par = [nombre + "_action_notification_third_party_name",
               nombre + "_action_notification_third_party_desc"]
        for idioma in ("spanish", "english"):
            presentes = [c in loc[idioma] for c in par]
            if all(presentes):
                print("[OK] %s loc %s third_party (pareja completa)"
                      % (etiqueta, idioma))
            elif any(presentes):
                violaciones.append(
                    (etiqueta,
                     "loc %s pareja third_party a medias: %s"
                     % (idioma, ", ".join(c for c, p in zip(par, presentes)
                                          if p))))
            else:
                avisos.append(
                    "%s: sin claves third_party en %s (hallazgo follow-up)"
                    % (etiqueta, idioma))


def main():
    violaciones = []
    avisos = []
    das, pactos, errores = bloques_da()
    for e in errores:
        print("VIOLACION infraestructura: %s" % e)
        print("DAs chequeadas: 0, violaciones: %d"
              % (len(errores)))
        return 1
    if not das:
        print("VIOLACION GUARD: 0 bloques de DA escaneados "
              "(anti-vacuidad M664)")
        print("DAs chequeadas: 0, violaciones: 1")
        return 1

    eventos_definidos = set()
    for path in glob.glob(os.path.join(EVENTS_DIR, "*.txt")):
        for linea in leer(path):
            m = re.match(r"^\s*([A-Za-z0-9_.]+)\s*=\s*\{", linea)
            if m:
                eventos_definidos.add(m.group(1))

    loc = cargar_loc()

    for bloque in das:
        chequear_estructura(bloque, violaciones)
        chequear_gate(bloque, violaciones)
        chequear_trigger_event(bloque, eventos_definidos, violaciones)
        chequear_save_scopes(bloque, violaciones)
        chequear_show_as_tooltip(bloque, violaciones)
        chequear_loc(bloque, loc, violaciones, avisos)

    for aviso in avisos:
        print("AVISO (no violacion): %s" % aviso)
    for etiqueta, mensaje in violaciones:
        print("VIOLACION %s: %s" % (etiqueta, mensaje))
    print("pactos omitidos (definiciones de pacto, no DAs): %d"
          % len(pactos))
    print("DAs chequeadas: %d, violaciones: %d"
          % (len(das), len(violaciones)))
    return 1 if violaciones else 0


if __name__ == "__main__":
    sys.exit(main())
