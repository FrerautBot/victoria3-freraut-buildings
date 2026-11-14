#!/usr/bin/env python3
"""Validador estatico del centro de minas (M730, orden-68, task-69).

Reglas:
  (a) pm_mining_center_base (common/production_methods/freraut_pms.txt),
      sub-bloque workforce_scaled: goods_input_tools_add = 10 (C-68-1: el
      "357" in-game es el agregado de ~23.8 niveles; el valor de archivo
      real es 15 y se edita ese). goods_output_{sulfur,iron,lead,coal,
      copper}_add = 30 y goods_output_gold_add = 10 (valores exactos de
      Lucas; sin regla de redondeo).
  (b) level_scaled del PM base: building_employment_laborers_add = 2000
      (M687-d). pm_mining_center_mechanized:
      building_employment_laborers_add = -375 INTACTO (M723: NO reescalar;
      con mecanizada el nivel queda 2000 - 375 = 1625; si Lucas quiere otra
      cosa, lo dira en validacion in-game). M687-a6 intacto:
      building_input_engines_add = 5 y
      building_output_transportation_add = 3.75 en la mecanizada.
  (c) bg_mining_center (common/building_groups/freraut_building_groups.txt):
      urbanization = 5 (M687-c3: urbanizacion PER NIVEL del edificio; el
      edificio no define employment ni urbanization propio, M687-c4).
  (d) Asserts NEGATIVOS: el PM minero base NO agrega country_minting_add
      (M687-b2: el oro vanilla es sector separado con minting; Lucas NO lo
      pidio); el mod NO define state_urbanization_add ni
      state_urbanization_per_level_add en common/ (M687-c1/c2); el PM base
      no agrega goods_input ni goods_output fuera de las 7 claves listadas
      (la transportation de la mecanizada es building_output_transportation,
      fuera del alcance del PM base).
  (e) Guard anti-vacuidad (M664): PM base, mecanizada o bg_mining_center
      ausentes, 0 claves detectadas o 0 archivos escaneados en common/ =
      fallo ruidoso.

Exit code: 0 = sin violaciones, 1 = violaciones.
Uso:  python tools/validar_minas.py
"""
import glob
import os
import re
import sys

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

PMS_FILE = os.path.join(BASE, "common", "production_methods",
                        "freraut_pms.txt")
GROUPS_FILE = os.path.join(BASE, "common", "building_groups",
                           "freraut_building_groups.txt")

PM_BASE = "pm_mining_center_base"
PM_MECH = "pm_mining_center_mechanized"
BG = "bg_mining_center"

EXPECTED_GOODS = {
    "goods_input_tools_add": 10,
    "goods_output_sulfur_add": 30,
    "goods_output_iron_add": 30,
    "goods_output_lead_add": 30,
    "goods_output_gold_add": 10,
    "goods_output_coal_add": 30,
    "goods_output_copper_add": 30,
}
EMPLOYMENT_BASE = 2000
EMPLOYMENT_MECH = -375
ENGINES_MECH = 5
TRANSPORT_MECH = 3.75
URBANIZATION = 5

BLOCK_HEADER_RE = re.compile(r"^(\S[\S ]*?)\s*=\s*\{\s*$")
KEY_VAL_RE = re.compile(r"^([a-z_][a-z_0-9]*)\s*=\s*(-?\d+(?:\.\d+)?)\s*$")


def strip_comment(line):
    return line.split("#", 1)[0].rstrip()


def leer(path):
    with open(path, encoding="utf-8-sig") as f:
        return f.read().split("\n")


def extraer_bloque(path, nombre):
    """Primer bloque `nombre = {` como lista [(linea_abs, texto)], o None."""
    lineas = leer(path)
    for n, raw in enumerate(lineas, 1):
        m = BLOCK_HEADER_RE.match(strip_comment(raw).strip())
        if not m or m.group(1) != nombre:
            continue
        prof = 1
        j = n
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
        return [(k, lineas[k - 1]) for k in range(n, j + 1)]
    return None


def sub_bloque(bloque, nombre):
    """Sub-bloque `nombre = {` dentro de `bloque` (lista (linea_abs, texto))."""
    for i, (_n, raw) in enumerate(bloque):
        m = BLOCK_HEADER_RE.match(strip_comment(raw).strip())
        if m and m.group(1) == nombre:
            prof = 0
            j = i
            while j < len(bloque):
                s = strip_comment(bloque[j][1]).strip()
                if s and s != "}":
                    if BLOCK_HEADER_RE.match(s):
                        prof += 1
                elif s == "}":
                    prof -= 1
                    if prof == 0:
                        break
                j += 1
            return bloque[i:j + 1]
    return None


def pares(bloque):
    """[(linea_abs, clave, valor)] de claves numericas dentro del bloque."""
    out = []
    for n, raw in bloque:
        m = KEY_VAL_RE.match(strip_comment(raw).strip())
        if m:
            out.append((n, m.group(1), float(m.group(2))))
    return out


def chequear_pm_base(violaciones):
    rel = "common/production_methods/freraut_pms.txt"
    bloque = extraer_bloque(PMS_FILE, PM_BASE)
    if bloque is None:
        print("VIOLACION GUARD: %s no encontrado en %s (anti-vacuidad M664)"
              % (PM_BASE, rel))
        return 1
    pares_bloque = pares(bloque)
    if not pares_bloque:
        print("VIOLACION GUARD: 0 claves detectadas en %s (anti-vacuidad "
              "M664)" % PM_BASE)
        return 1
    ws = sub_bloque(bloque, "workforce_scaled")
    ls = sub_bloque(bloque, "level_scaled")
    if ws is None or ls is None:
        violaciones.append(
            (rel, "%s sin workforce_scaled/level_scaled (workforce=%s, "
                  "level=%s)" % (PM_BASE, ws is not None, ls is not None)))
        return 0
    ws_lineas = {n for n, _raw in ws}
    ls_lineas = {n for n, _raw in ls}
    for clave, esperado in EXPECTED_GOODS.items():
        hallados = [(n, v) for n, c, v in pares_bloque if c == clave]
        if len(hallados) == 1 and hallados[0][1] == float(esperado) \
                and hallados[0][0] in ws_lineas:
            print("[OK] %s = %g workforce_scaled (%s:%d)"
                  % (clave, esperado, rel, hallados[0][0]))
        else:
            violaciones.append(
                (rel, "%s esperado %g en workforce_scaled, encontrado %s"
                 % (clave, esperado, hallados)))
    emp = [(n, v) for n, c, v in pares_bloque
           if c == "building_employment_laborers_add"]
    if len(emp) == 1 and emp[0][1] == float(EMPLOYMENT_BASE) \
            and emp[0][0] in ls_lineas:
        print("[OK] building_employment_laborers_add = %d level_scaled "
              "(%s:%d)" % (EMPLOYMENT_BASE, rel, emp[0][0]))
    else:
        violaciones.append(
            (rel, "building_employment_laborers_add esperado %d en "
                  "level_scaled del PM base, encontrado %s"
             % (EMPLOYMENT_BASE, emp)))
    for n, c, v in pares_bloque:
        if c.startswith("goods_output_") and c not in EXPECTED_GOODS:
            violaciones.append(
                (rel, "goods_output fuera de los 6 permitidos en el PM "
                      "minero base: %s = %g (%s:%d)" % (c, v, rel, n)))
        if c.startswith("goods_input_") and c != "goods_input_tools_add":
            violaciones.append(
                (rel, "goods_input fuera del permitido en el PM minero "
                      "base: %s = %g (%s:%d)" % (c, v, rel, n)))
    if any(c == "country_minting_add" for _n, c, _v in pares_bloque):
        violaciones.append(
            (rel, "country_minting_add en el PM minero (M687-b2: NO agregar "
                  "minting; Lucas no lo pidio)"))
    else:
        print("[OK] M687-b2 PM minero base sin country_minting_add")
    return 0


def chequear_mecanizada(violaciones):
    rel = "common/production_methods/freraut_pms.txt"
    bloque = extraer_bloque(PMS_FILE, PM_MECH)
    if bloque is None:
        print("VIOLACION GUARD: %s no encontrado en %s (anti-vacuidad M664)"
              % (PM_MECH, rel))
        return 1
    pares_bloque = pares(bloque)
    if not pares_bloque:
        print("VIOLACION GUARD: 0 claves detectadas en %s (anti-vacuidad "
              "M664)" % PM_MECH)
        return 1
    emp = [(n, v) for n, c, v in pares_bloque
           if c == "building_employment_laborers_add"]
    if len(emp) == 1 and emp[0][1] == float(EMPLOYMENT_MECH):
        print("[OK] M723 mecanizada building_employment_laborers_add = %d "
              "intacto (%s:%d) -> nivel mecanizado 2000-375 = 1625"
              % (EMPLOYMENT_MECH, rel, emp[0][0]))
    else:
        violaciones.append(
            (rel, "M723 mecanizada esperado -375 intacto, encontrado %s"
             % emp))
    motores = [(n, v) for n, c, v in pares_bloque
               if c == "building_input_engines_add"]
    if len(motores) == 1 and motores[0][1] == float(ENGINES_MECH):
        print("[OK] M687-a6 building_input_engines_add = %d intacto (%s:%d)"
              % (ENGINES_MECH, rel, motores[0][0]))
    else:
        violaciones.append(
            (rel, "M687-a6 building_input_engines_add esperado %d intacto, "
                  "encontrado %s" % (ENGINES_MECH, motores)))
    trans = [(n, v) for n, c, v in pares_bloque
             if c == "building_output_transportation_add"]
    if len(trans) == 1 and trans[0][1] == float(TRANSPORT_MECH):
        print("[OK] M687-a6 building_output_transportation_add = %g intacto "
              "(%s:%d)" % (TRANSPORT_MECH, rel, trans[0][0]))
    else:
        violaciones.append(
            (rel, "M687-a6 building_output_transportation_add esperado %g "
                  "intacto, encontrado %s" % (TRANSPORT_MECH, trans)))
    return 0


def chequear_grupo(violaciones):
    rel = "common/building_groups/freraut_building_groups.txt"
    bloque = extraer_bloque(GROUPS_FILE, BG)
    if bloque is None:
        print("VIOLACION GUARD: %s no encontrado en %s (anti-vacuidad M664)"
              % (BG, rel))
        return 1
    pares_bloque = pares(bloque)
    if not pares_bloque:
        print("VIOLACION GUARD: 0 claves detectadas en %s (anti-vacuidad "
              "M664)" % BG)
        return 1
    urb = [(n, v) for n, c, v in pares_bloque if c == "urbanization"]
    if len(urb) == 1 and urb[0][1] == float(URBANIZATION):
        print("[OK] M687-c3 bg_mining_center urbanization = %d por nivel "
              "(%s:%d)" % (URBANIZATION, rel, urb[0][0]))
    else:
        violaciones.append(
            (rel, "bg_mining_center urbanization esperado %d, encontrado %s"
             % (URBANIZATION, urb)))
    return 0


def chequear_urbanization_keys(violaciones):
    archivos = sorted(glob.glob(os.path.join(BASE, "common", "**", "*.txt"),
                                recursive=True))
    if not archivos:
        print("VIOLACION GUARD: 0 archivos escaneados en common/ "
              "(anti-vacuidad M664)")
        return 1
    for clave in ("state_urbanization_add", "state_urbanization_per_level_add"):
        hits = []
        for path in archivos:
            for n, raw in enumerate(leer(path), 1):
                if clave in strip_comment(raw):
                    hits.append("%s:%d" % (os.path.relpath(path, BASE), n))
        if hits:
            violaciones.append(
                ("common/", "%s presente en %s (M687-c1/c2: no usar; la "
                            "urbanizacion per-level es el campo urbanization "
                            "del building group)" % (clave, ", ".join(hits))))
        else:
            print("[OK] M687-c1/c2 %s ausente en todo common/ (%d archivos "
                  "escaneados)" % (clave, len(archivos)))
    return 0


def main():
    violaciones = []
    chequear_pm_base(violaciones)
    chequear_mecanizada(violaciones)
    chequear_grupo(violaciones)
    chequear_urbanization_keys(violaciones)

    for etiqueta, mensaje in violaciones:
        print("VIOLACION %s: %s" % (etiqueta, mensaje))
    print("violaciones: %d" % len(violaciones))
    return 1 if violaciones else 0


if __name__ == "__main__":
    sys.exit(main())
