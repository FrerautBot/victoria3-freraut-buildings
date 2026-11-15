#!/usr/bin/env python3
"""Meta-test del validador de edificios (M777, task-70).

Reglas:
  (a) el fixture tools/fixtures/edificios_pre_70/ es el estado ANTES de
      task-70 (violaciones esperadas): validar_edificios.py sobre esa raiz
      DEBE salir con exit != 0; si el fixture pasa limpio, el validador
      perdio capacidad de deteccion y este runner falla.
  (b) la raiz real del repo (post-task) DEBE salir con exit == 0; si el
      repo vigente falla, el runner falla.

Nota: este runner itera SOLO el fixture de edificios (no todos los
directorios de tools/fixtures/), para no solapar con el meta-test de
tributos (test_validator_fixtures.py).

Exit code: 0 = meta-test verde, 1 = meta-test rojo.
Uso:  python tools/test_validator_fixtures_edificios.py
"""
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.dirname(HERE)
FIXTURE = os.path.join(HERE, "fixtures", "edificios_pre_70")
VALIDATOR = os.path.join(HERE, "validar_edificios.py")


def ejecutar(raiz):
    proc = subprocess.run(
        [sys.executable, VALIDATOR, raiz],
        capture_output=True, text=True, encoding="utf-8")
    print("=== validar_edificios.py raiz=%s (exit %d) ==="
          % (raiz, proc.returncode))
    print(proc.stdout, end="")
    if proc.stderr:
        print("--- stderr ---")
        print(proc.stderr, end="")
    print("=== fin raiz=%s ===" % raiz)
    return proc.returncode


def main():
    fallos = []
    if not os.path.isdir(FIXTURE):
        print("VIOLACION META-TEST: fixture edificios_pre_70 no existe "
              "en tools/fixtures/")
        return 1
    exit_fixture = ejecutar(FIXTURE)
    if exit_fixture == 0:
        fallos.append("edificios_pre_70 paso limpio (se esperaba exit != 0)")
    else:
        print("[OK] M777 fixture edificios_pre_70 en rojo como se esperaba")
    exit_vigente = ejecutar(BASE)
    if exit_vigente != 0:
        fallos.append("repo vigente %s fallo (se esperaba exit == 0)" % BASE)
    else:
        print("[OK] M777 repo vigente verde (exit 0)")
    for f in fallos:
        print("VIOLACION META-TEST: %s" % f)
    print("meta-test edificios: %s (fixture exit %d, repo vigente exit %d)"
          % ("VERDE" if not fallos else "ROJO", exit_fixture, exit_vigente))
    return 1 if fallos else 0


if __name__ == "__main__":
    sys.exit(main())
