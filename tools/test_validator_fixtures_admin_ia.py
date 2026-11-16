#!/usr/bin/env python3
"""Meta-test del validador de administraciones IA (M777, task-72 Parte D).

Reglas:
  (a) el fixture tools/fixtures/admin_ia_pre_69/ es el estado ANTES de
      orden-69 (violaciones esperadas): validar_admin_ia.py sobre esa raiz
      DEBE salir con exit != 0; si el fixture pasa limpio, el validador
      perdio capacidad de deteccion y este runner falla.
  (b) la raiz real del repo (post-task) DEBE salir con exit == 0; si el
      repo vigente falla, el runner falla.

Exit code: 0 = meta-test verde, 1 = meta-test rojo.
Uso:  python tools/test_validator_fixtures_admin_ia.py
"""
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.dirname(HERE)
FIXTURE = os.path.join(HERE, "fixtures", "admin_ia_pre_69")
VALIDATOR = os.path.join(HERE, "validar_admin_ia.py")


def ejecutar(raiz):
    proc = subprocess.run(
        [sys.executable, VALIDATOR, raiz],
        capture_output=True, text=True, encoding="utf-8")
    print("=== validar_admin_ia.py raiz=%s (exit %d) ==="
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
        print("VIOLACION META-TEST: fixture admin_ia_pre_69 no existe "
              "en tools/fixtures/")
        return 1
    exit_fixture = ejecutar(FIXTURE)
    if exit_fixture == 0:
        fallos.append("admin_ia_pre_69 paso limpio (se esperaba exit != 0)")
    else:
        print("[OK] M777 fixture admin_ia_pre_69 en rojo como se esperaba")
    exit_vigente = ejecutar(BASE)
    if exit_vigente != 0:
        fallos.append("repo vigente %s fallo (se esperaba exit == 0)" % BASE)
    else:
        print("[OK] M777 repo vigente verde (exit 0)")
    for f in fallos:
        print("VIOLACION META-TEST: %s" % f)
    print("meta-test admin_ia: %s (fixture exit %d, repo vigente exit %d)"
          % ("VERDE" if not fallos else "ROJO", exit_fixture, exit_vigente))
    return 1 if fallos else 0


if __name__ == "__main__":
    sys.exit(main())
