#!/usr/bin/env python3
"""Validador de exclusividad de familias de pactos (orden-64, Parte B).

Con el fin de la exclusion mutua tributo/desarrollo se verifica que:
  (a) ninguna opcion de events/freraut_tribute_events.txt remueve pactos de
      desarrollo (freraut_remove_all_dev_pacts);
  (b) ninguna opcion de events/freraut_dev_events.txt remueve pactos de
      tributo (freraut_remove_all_tribute_pacts);
  (c) las 3 DA de regimen (colonial / explotacion / unificar cultura) de
      common/diplomatic_actions/freraut_administration_actions.txt conservan
      freraut_remove_all_tribute_pacts y no vuelven a remover
      freraut_remove_all_dev_pacts.

Exit code: 0 = sin violaciones, 1 = violaciones.
Uso:  python tools/validar_familias.py
"""
import os
import re
import sys

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

TRIBUTO = "events/freraut_tribute_events.txt"
DEV = "events/freraut_dev_events.txt"
ADMIN = "common/diplomatic_actions/freraut_administration_actions.txt"

DAS_REGIMEN = (
    "freraut_da_colonial_regime",
    "freraut_da_explotation_regime",
    "freraut_da_unify_culture",
)

BLOCK_RE = re.compile(r"^(\S[\S ]*?)\s*=\s*\{$")


def strip_comment(line):
    return line.split("#", 1)[0].rstrip()


def leer(path):
    with open(os.path.join(BASE, path), encoding="utf-8-sig") as f:
        return f.read().split("\n")


def bloques(path, cabecera=None):
    """Devuelve (nombre, linea_inicio, linea_fin, texto) por cada bloque cuya
    cabecera coincide con `cabecera` (todos si es None). Lineas 1-based y el
    rango es [inicio, fin) para indexar con lineas[inicio-1:fin-1]."""
    lineas = leer(path)
    pila = []
    resultado = []
    for n, raw in enumerate(lineas, 1):
        line = strip_comment(raw).strip()
        if not line:
            continue
        if line == "}":
            if pila:
                nombre, inicio = pila.pop()
                if cabecera is None or nombre == cabecera:
                    resultado.append((nombre, inicio, n,
                                      "\n".join(lineas[inicio - 1:n - 1])))
            continue
        m = BLOCK_RE.match(line)
        if m:
            pila.append((m.group(1), n))
    return resultado


def linea_de(texto_bloque, aguja, linea_inicio):
    for i, linea in enumerate(texto_bloque.split("\n"), 1):
        if aguja in strip_comment(linea):
            return linea_inicio + i - 1
    return None


def main():
    violaciones = 0
    total_opciones = 0

    reglas = [
        (TRIBUTO, "freraut_remove_all_dev_pacts",
         "opcion de tributo remueve pactos de desarrollo"),
        (DEV, "freraut_remove_all_tribute_pacts",
         "opcion de desarrollo remueve pactos de tributo"),
    ]
    for path, prohibido, desc in reglas:
        opciones = bloques(path, "option")
        total_opciones += len(opciones)
        for nombre, inicio, fin, texto in opciones:
            if prohibido in texto:
                violaciones += 1
                print("VIOLACION %s: %s (linea %d)"
                      % (path, desc, linea_de(texto, prohibido, inicio)))

    das = bloques(ADMIN)
    regimenes = [b for b in das if b[0] in DAS_REGIMEN]
    for nombre, inicio, fin, texto in regimenes:
        if "freraut_remove_all_tribute_pacts" not in texto:
            violaciones += 1
            print("VIOLACION %s: %s perdio freraut_remove_all_tribute_pacts"
                  % (ADMIN, nombre))
        if "freraut_remove_all_dev_pacts" in texto:
            violaciones += 1
            print("VIOLACION %s: %s volvio a remover dev (linea %d)"
                  % (ADMIN, nombre,
                     linea_de(texto, "freraut_remove_all_dev_pacts", inicio)))

    print("opciones chequeadas: %d, DA de regimen chequeadas: %d, "
          "violaciones: %d" % (total_opciones, len(regimenes), violaciones))
    return 1 if violaciones else 0


if __name__ == "__main__":
    sys.exit(main())
