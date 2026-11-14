#!/usr/bin/env python3
"""Meta-test del validador de tributos (M750, task-67b).

Reglas:
  (a) cada directorio de tools/fixtures/ es un estado ANTES de un fix
      (violaciones esperadas): validar_tributos.py sobre esa raiz DEBE
      salir con exit != 0; si un fixture pasa limpio, el validador perdio
      capacidad de deteccion y este runner falla.
  (b) la raiz real del repo (post-fix) DEBE salir con exit == 0; si el repo
      vigente falla, el runner falla.

Exit code: 0 = meta-test verde, 1 = meta-test rojo.
Uso:  python tools/test_validator_fixtures.py
"""
import glob
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.dirname(HERE)
FIXTURES_DIR = os.path.join(HERE, "fixtures")
VALIDATOR = os.path.join(HERE, "validar_tributos.py")


def ejecutar(raiz):
    proc = subprocess.run(
        [sys.executable, VALIDATOR, raiz],
        capture_output=True, text=True, encoding="utf-8")
    print("=== validar_tributos.py raiz=%s (exit %d) ==="
          % (raiz, proc.returncode))
    print(proc.stdout, end="")
    if proc.stderr:
        print("--- stderr ---")
        print(proc.stderr, end="")
    print("=== fin raiz=%s ===" % raiz)
    return proc.returncode


def main():
    fallos = []
    fixtures = sorted(glob.glob(os.path.join(FIXTURES_DIR, "*")))
    dirs = [d for d in fixtures if os.path.isdir(d)]
    if not dirs:
        print("VIOLACION META-TEST: tools/fixtures/ sin directorios de "
              "fixture")
        return 1
    for d in dirs:
        exit_code = ejecutar(d)
        if exit_code == 0:
            fallos.append("%s paso limpio (se esperaba exit != 0)"
                          % os.path.basename(d))
        else:
            print("[OK] M750 fixture %s en rojo como se esperaba"
                  % os.path.basename(d))
    exit_vigente = ejecutar(BASE)
    if exit_vigente != 0:
        fallos.append("repo vigente %s fallo (se esperaba exit == 0)" % BASE)
    else:
        print("[OK] M750 repo vigente verde (exit 0)")
    for f in fallos:
        print("VIOLACION META-TEST: %s" % f)
    print("meta-test: %s (%d fixtures, repo vigente exit %d)"
          % ("VERDE" if not fallos else "ROJO", len(dirs), exit_vigente))
    return 1 if fallos else 0


if __name__ == "__main__":
    sys.exit(main())
