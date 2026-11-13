#!/usr/bin/env python3
"""Check de monotonia del balance /4 (M560, orden-61).

Lee common/production_methods/freraut_pms.txt, agrupa los valores por PM y
por clave, y verifica:
  1. ningun building_employment_* <= 0 fuera de los casos declarados
     (los PM de la tabla del task-58 que reducen empleo: ver ALLOWLIST);
  2. ningun goods_output_* negativo (0 casos declarados: cualquier negativo
     es defecto);
  3. consistencia /4: cada goods_output_*_add y building_employment_*_add
     debe ser multiplo exacto de 0.25 (valor * 4 entero).
NO modifica valores: solo reporta. Exit code: 0 = sin defectos, 1 = defectos.

Uso:  python tools/validar_balance.py [ruta_freraut_pms.txt]
"""
import re
import sys
from pathlib import Path

DEFAULT = Path(__file__).resolve().parent.parent / "common" / "production_methods" / "freraut_pms.txt"

# Casos declarados del balance /4 (tabla task-58): PMs con empleo negativo
# (reduccion de mano de obra). Valores negativos de empleo SOLO se permiten
# dentro de estos PMs (lineas del archivo vigente: 125-126, 1083, 1131-1133).
ALLOWLIST_NEG_EMPLEO = {
    "pm_public_health_victorian",  # -250/-375 en :125-126; el comentario :124
    # dice "contrata empleados adicionales" pero los valores restan: posible
    # inversion de signo pendiente de confirmar con Lucas (no se corrige aqui).
    "pm_mining_center_mechanized",
    "pm_manufacturing_center_specialized_tools",
}

VALUE_RE = re.compile(r"^\s*([a-zA-Z0-9_]+)\s*=\s*(-?[0-9]+(?:\.[0-9]+)?)\s*$")
BLOCK_RE = re.compile(r"^([a-zA-Z0-9_]+)\s*=\s*\{")


def parse_blocks(path):
    lines = path.read_text(encoding="utf-8-sig").splitlines()
    blocks = []
    current = None
    for i, line in enumerate(lines, 1):
        if line.lstrip().startswith("#") or not line.strip():
            continue
        m = BLOCK_RE.match(line)
        if m:
            current = {"name": m.group(1), "start": i, "values": []}
            blocks.append(current)
            continue
        vm = VALUE_RE.match(line)
        if vm and current is not None:
            current["values"].append((i, vm.group(1), float(vm.group(2))))
    return blocks


def is_mult_of_quarter(v, tol=1e-6):
    return abs(v * 4 - round(v * 4)) < tol


def main():
    path = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT
    if not path.exists():
        print(f"ERROR: no existe {path}")
        return 1

    blocks = parse_blocks(path)
    defectos = []
    for b in blocks:
        for line, key, value in b["values"]:
            if key.startswith("goods_output") and value < 0:
                defectos.append((b["name"], line, key, value, "goods_output negativo"))
            if key.startswith("building_employment") and value <= 0:
                if b["name"] not in ALLOWLIST_NEG_EMPLEO:
                    defectos.append((b["name"], line, key, value,
                                     "empleo <= 0 fuera de allowlist"))
            if (key.startswith("goods_output") or key.startswith("building_employment")) \
                    and not is_mult_of_quarter(value):
                defectos.append((b["name"], line, key, value,
                                 f"rompe regla /4 (x4 = {value * 4})"))
            if key.startswith("goods_input") and value < 0:
                defectos.append((b["name"], line, key, value, "goods_input negativo"))

    print(f"archivo: {path}")
    print(f"PMs: {len(blocks)}")
    n_out = sum(1 for b in blocks for _, k, _ in b["values"] if k.startswith("goods_output"))
    n_in = sum(1 for b in blocks for _, k, _ in b["values"] if k.startswith("goods_input"))
    n_emp = sum(1 for b in blocks for _, k, _ in b["values"] if k.startswith("building_employment"))
    print(f"claves: goods_output={n_out}, goods_input={n_in}, building_employment={n_emp}")

    neg_emp = [(b["name"], l, k, v) for b in blocks for l, k, v in b["values"]
               if k.startswith("building_employment") and v <= 0]
    if neg_emp:
        print("\nempleo negativo (declarados, dentro de allowlist):")
        for name, l, k, v in neg_emp:
            ok = "OK" if name in ALLOWLIST_NEG_EMPLEO else "FUERA"
            print(f"  {name}:{l} {k} = {v} [{ok}]")

    if defectos:
        print(f"\nDEFECTOS ({len(defectos)}):")
        for name, line, key, value, motivo in defectos:
            print(f"  {name}:{line} {key} = {value} -> {motivo}")
    else:
        print("\nSin defectos: balance /4 monotono sobre el archivo vigente.")
    return 1 if defectos else 0


if __name__ == "__main__":
    sys.exit(main())
