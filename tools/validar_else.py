#!/usr/bin/env python3
"""Validador estructural de else/else_if (M557, orden-61).

Regla: todo `else = {` / `else_if = {` debe tener un hermano `if`/`else_if`
abierto al mismo nivel de indentado (tabs) en su scope. Recorre todos los
*.txt del repo del mod (o los paths pasados por CLI) y reporta OK por bloque
o lista de defectos con linea. Exit code: 0 = sin defectos, 1 = defectos.

Uso:  python tools/validar_else.py [path...]
"""
import re
import sys
from pathlib import Path

COND_RE = re.compile(r"^(if|else_if|else)\s*=\s*\{")


def indent_level(line: str) -> int:
    return len(line) - len(line.lstrip("\t"))


def strip_comment(line: str) -> str:
    return line.split("#", 1)[0].rstrip()


def check_lines(lines, source):
    """Devuelve (resultados, defectos) para una lista de lineas."""
    resultados = []
    defectos = []
    for i, raw in enumerate(lines, 1):
        line = strip_comment(raw)
        m = COND_RE.match(line.strip())
        if not m:
            continue
        kw = m.group(1)
        level = indent_level(raw)
        if kw == "if":
            resultados.append((source, i, kw, "OK", None))
            continue
        # else / else_if: buscar hermano hacia atras al mismo nivel
        hermano = None
        for j in range(i - 2, -1, -1):
            prev_raw = lines[j]
            prev = strip_comment(prev_raw)
            if not prev.strip():
                continue
            lvl = indent_level(prev_raw)
            if lvl < level:
                break  # scope cerrado sin hermano condicional
            if lvl == level:
                if prev.strip() == "}" or prev.strip().startswith("}"):
                    continue  # cierra el cuerpo de la rama anterior: seguir subiendo
                hermano = prev.strip()
                break
        if hermano is None or not COND_RE.match(hermano):
            defectos.append((source, i, kw, level,
                             hermano if hermano is not None else "(scope cerrado)"))
            resultados.append((source, i, kw, "DEFECTO", hermano))
        elif COND_RE.match(hermano).group(1) in ("if", "else_if"):
            resultados.append((source, i, kw, "OK", hermano))
        else:
            defectos.append((source, i, kw, level, hermano))
            resultados.append((source, i, kw, "DEFECTO", hermano))
    return resultados, defectos


def main():
    if len(sys.argv) > 1:
        roots = [Path(a) for a in sys.argv[1:]]
    else:
        roots = [Path(__file__).resolve().parent.parent]

    archivos = []
    for root in roots:
        if root.is_file() and root.suffix == ".txt":
            archivos.append(root)
        elif root.is_dir():
            archivos.extend(
                p for p in sorted(root.rglob("*.txt"))
                if ".git" not in p.parts
            )

    total_ok = 0
    todos_defectos = []
    for f in archivos:
        lines = f.read_text(encoding="utf-8-sig").splitlines()
        resultados, defectos = check_lines(lines, str(f))
        n_cond = sum(1 for r in resultados if r[2] in ("else", "else_if"))
        n_ok = sum(1 for r in resultados
                   if r[2] in ("else", "else_if") and r[3] == "OK")
        total_ok += n_ok
        todos_defectos.extend(defectos)
        if n_cond:
            print(f"{f}: {n_cond} else/else_if, {n_ok} OK, {len(defectos)} defectos")
        for d in defectos:
            print(f"  DEFECTO {d[0]}:{d[1]} {d[2]} (nivel {d[3]}): "
                  f"hermano previo = {d[4]!r}")

    print(f"\nTOTAL: {total_ok} else/else_if OK, {len(todos_defectos)} defectos")
    return 1 if todos_defectos else 0


if __name__ == "__main__":
    sys.exit(main())
