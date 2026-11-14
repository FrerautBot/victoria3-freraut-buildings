#!/usr/bin/env python3
"""Validador de direccion del income transfer de pactos freraut (M623, orden-63).

Regla: en los pactos freraut el primer pais (actor) es el VASALLO y el segundo
(recipiente) es el SENOR, porque los create_diplomatic_pact se ejecutan dentro
de un scope de sujeto con `country = root`. Por lo tanto, segun la primitiva
(game/common/diplomatic_actions/diplomatic_action.md:62-63):
  - tributo (vasallo paga al senor % de SU ingreso): par (yes, no)
  - inversion en desarrollo (senor paga al vasallo % de SU ingreso): par (no, yes)

Chequeos por cada create_diplomatic_pact en events/freraut_tribute_events.txt,
events/freraut_dev_events.txt, events/freraut_union_events.txt y
common/diplomatic_actions/freraut_administration_actions.txt:
  1. el tipo del pacto tiene definicion con par de income transfer en el DA
  2. el par de la definicion coincide con el esperado para el tipo
  3. el create esta dentro de un scope de sujeto (freraut_tribute_subject /
     freraut_dev_subject / target_country / every_subject_or_below) y el
     recipiente es country = root

Exit code: 0 = sin violaciones, 1 = violaciones.
Uso:  python tools/validar_direccion.py
"""
import os
import re
import sys

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

FILES = [
    "events/freraut_tribute_events.txt",
    "events/freraut_dev_events.txt",
    "events/freraut_union_events.txt",
    "common/diplomatic_actions/freraut_administration_actions.txt",
]
DA_FILE = "common/diplomatic_actions/freraut_administration_actions.txt"

ACTOR_SCOPES = (
    "scope:freraut_tribute_subject",
    "scope:freraut_dev_subject",
    "scope:target_country",
    "every_subject_or_below",
)

BLOCK_RE = re.compile(r"^(\S[\S ]*?)\s*=\s*\{$")
FIELD_TYPE_RE = re.compile(r"^type\s*=\s*(\S+)$")
FIELD_COUNTRY_RE = re.compile(r"^country\s*=\s*(\S+)$")
FIELD_GETS_RE = re.compile(r"^second_country_gets_income_transfer\s*=\s*(yes|no)$")
FIELD_BASED_RE = re.compile(r"^income_transfer_based_on_second_country\s*=\s*(yes|no)$")


def strip_comment(line):
    return line.split("#", 1)[0].rstrip()


def leer(path):
    with open(os.path.join(BASE, path), encoding="utf-8-sig") as f:
        return f.read().split("\n")


def extraer_definiciones():
    """Mapa tipo -> (gets, based) leido de las definiciones de DA."""
    definiciones = {}
    pila = []
    da_actual = None
    in_pact = False
    par = {}
    for n, raw in enumerate(leer(DA_FILE), 1):
        line = strip_comment(raw).strip()
        if not line:
            continue
        if line == "}":
            if pila:
                cab = pila.pop()
                if cab == "pact":
                    in_pact = False
                    if da_actual and par:
                        definiciones[da_actual] = (
                            par.get("gets", "?"), par.get("based", "?"))
                    par = {}
                elif cab == da_actual and cab is not None:
                    da_actual = None
            continue
        m = BLOCK_RE.match(line)
        if m:
            cab = m.group(1)
            pila.append(cab)
            if not in_pact and da_actual is None and len(pila) == 1:
                da_actual = cab
            elif cab == "pact" and da_actual is not None:
                in_pact = True
            continue
        if in_pact:
            g = FIELD_GETS_RE.match(line)
            if g:
                par["gets"] = g.group(1)
            b = FIELD_BASED_RE.match(line)
            if b:
                par["based"] = b.group(1)
    return definiciones


def esperado(tipo):
    if tipo.startswith("freraut_da_tribute"):
        return ("yes", "no")
    if tipo.startswith("freraut_da_dev_"):
        return ("no", "yes")
    return None


def escanear_creaciones(definiciones):
    """Devuelve lista de (fuente, linea, tipo, actor, recipiente, par, esperado, veredicto)."""
    resultados = []
    violaciones = 0
    for path in FILES:
        pila = []
        for n, raw in enumerate(leer(path), 1):
            line = strip_comment(raw).strip()
            if not line:
                continue
            if line == "}":
                if pila:
                    cab = pila.pop()
                    if cab == "create_diplomatic_pact":
                        actor = next(
                            (c for c in reversed(pila) if c in ACTOR_SCOPES), "?")
                        recipiente = datos.get("country", "?")
                        tipo = datos.get("type", "?")
                        exp = esperado(tipo)
                        if exp is None:
                            veredicto = "no-aplica"
                        else:
                            par_def = definiciones.get(tipo)
                            if par_def is None:
                                veredicto = "VIOLACION: tipo sin definicion"
                            elif actor not in ACTOR_SCOPES:
                                veredicto = "VIOLACION: create fuera de scope de sujeto"
                            elif recipiente != "root":
                                veredicto = "VIOLACION: recipiente != root"
                            elif par_def != exp:
                                veredicto = "VIOLACION: par %s != esperado %s" % (par_def, exp)
                            else:
                                veredicto = "OK"
                            if veredicto != "OK":
                                violaciones += 1
                        resultados.append((path, n, tipo, actor, recipiente,
                                           definiciones.get(tipo), exp, veredicto))
                        datos = {}
                continue
            m = BLOCK_RE.match(line)
            if m:
                cab = m.group(1)
                pila.append(cab)
                if cab == "create_diplomatic_pact":
                    datos = {}
                continue
            if pila and pila[-1] == "create_diplomatic_pact":
                t = FIELD_TYPE_RE.match(line)
                if t:
                    datos["type"] = t.group(1)
                c = FIELD_COUNTRY_RE.match(line)
                if c:
                    datos["country"] = c.group(1)
    return resultados, violaciones


def main():
    definiciones = extraer_definiciones()
    resultados, violaciones = escanear_creaciones(definiciones)
    for fuente, linea, tipo, actor, recipiente, par_def, exp, veredicto in resultados:
        print("%s:%d  tipo=%s actor=%s recipiente=%s par_definicion=%s esperado=%s -> %s"
              % (fuente, linea, tipo, actor, recipiente, par_def, exp, veredicto))
    print("pactos chequeados: %d, violaciones: %d" % (len(resultados), violaciones))
    return 1 if violaciones else 0


if __name__ == "__main__":
    sys.exit(main())
