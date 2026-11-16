#!/usr/bin/env python3
"""Validador estatico de administraciones IA (orden-69, task-72 Parte D).

Reglas:
  (1) cantidad: bloques freraut_ai_admin_region_* en
      common/decisions/freraut_ai_admin_decisions.txt == regiones
      estrategicas TERRESTRES vanilla (36, CORR-3; leidas en runtime de
      game/common/strategic_regions/*.txt excluyendo water_strategic_regions).
      Guard anti-vacuidad (M664): 0 regiones vanilla o 0 bloques mod =
      fallo ruidoso.
  (2) esqueleto por bloque: possible con is_ai = yes e is_subject = no;
      ai_chance con base = 0, >= 4 modifiers, cada add <= 30 y suma <= 82
      (techo M803); gate de cooldown M803 en possible (NOT has_variable
      freraut_ai_admin_cooldown) y set_variable con name =
      freraut_ai_admin_cooldown + months = 12 en when_taken; when_taken con
      set_variable freraut_ai_admin_group, region = sr:region_X acorde al
      nombre del bloque y create_dynamic_country con cede_state_trigger
      has_variable freraut_ai_admin_group.
  (3) transformacion en on_created: cadena D6 completa (9 pares
      has_law/activate_law, variantes antes del padre, ley del padre al
      final); Parte C rama explotacion (law_colonial_exploitation,
      freraut_admin_exploitation, freraut_remove_all_tribute_pacts,
      freraut_da_tribute, add_loyalists 0.02) y rama colonia
      (law_frontier_colonization, freraut_remove_all_tribute_pacts,
      transferencia de culturas del senor); activate_law de
      law_colonial_administration aparece EXACTAMENTE 1 vez (solo la rama
      D6; excepcion documentada al anti-deriva D6); freraut_admin_base_liberty
      presente; CORR-4 remove_variable despues del transform. Aplica a los
      36 on_created de Parte A y al de Parte B; el on_created del jugador
      (freraut_approve_autonomy) exige D6 y NO Parte C. Anti-drift: las DAs
      freraut_da_colonial_regime / freraut_da_explotation_regime conservan
      sus claves intactas.
  (4) consolidacion: freraut_da_cease_autonomy sin will_propose
      `always = no`; accept_effect con set_variable
      freraut_ai_consolidation_group ANTES de annex_with_incorporation y
      create_dynamic_country DESPUES (orden de lineas).
  (5) NO-REGRESION: ai_chance base 0 de freraut_approve_autonomy intacto;
      ai_weight value 0 de ambos decretos intacto (D2).
  (6) M804 contenedores: ai_chance SOLO en decisions freraut; ai_weight
      SOLO en decrees freraut; evaluation_chance/propose_score/will_propose
      SOLO en diplomatic_actions freraut; existencia de cada clave AI en el
      motor chequeada contra el arbol vanilla (aviso si el arbol no existe).
  (7) M750: raiz opcional por argumento (fixtures del red test).

Exit code: 0 = sin violaciones, 1 = violaciones.
Uso:  python tools/validar_admin_ia.py [raiz_mod]
"""
import glob
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.dirname(HERE)
ROOT = os.path.abspath(sys.argv[1]) if len(sys.argv) > 1 else BASE

V3_GAME = os.environ.get(
    "FRERAUT_V3_GAME",
    "C:/Program Files (x86)/Steam/steamapps/common/Victoria 3/game")

DECISIONS_AI = os.path.join(ROOT, "common", "decisions",
                            "freraut_ai_admin_decisions.txt")
DECISIONS_JUGADOR = os.path.join(ROOT, "common", "decisions",
                                 "freraut_autonomy_decisions.txt")
DA_FILE = os.path.join(ROOT, "common", "diplomatic_actions",
                       "freraut_administration_actions.txt")
DECREES_FILE = os.path.join(ROOT, "common", "decrees",
                            "freraut_autonomy_decrees.txt")

TERRESTRIAL_REGION_FILES = [
    "african_strategic_regions.txt",
    "east_asia_strategic_regions.txt",
    "europe_strategic_regions.txt",
    "north_america_strategic_regions.txt",
    "south_america_strategic_regions.txt",
    "west_south_asia_strategic_regions.txt",
]

D6_LAWS = [
    "law_social_monarchy", "law_presidential_republic",
    "law_parliamentary_republic", "law_theocracy", "law_council_republic",
    "law_corporate_state", "law_chiefdom", "law_colonial_administration",
    "law_monarchy",
]

EXPLOTACION_KEYS = [
    "activate_law = law_type:law_colonial_exploitation",
    "name = freraut_admin_exploitation",
    "freraut_remove_all_tribute_pacts = yes",
    "type = freraut_da_tribute",
    "add_loyalists",
    "value = 0.02",
]
COLONIA_KEYS = [
    "activate_law = law_type:law_frontier_colonization",
    "freraut_remove_all_tribute_pacts = yes",
    "is_primary_culture_of = root",
    "add_primary_culture = scope:freraut_admin_temp_culture",
]
BASE_LIBERTY = "name = freraut_admin_base_liberty"

BLOCK_HEADER_RE = re.compile(r"^(\S[\S ]*?)\s*=\s*\{\s*$")


def strip_comment(line):
    return line.split("#", 1)[0].rstrip()


def leer(path):
    with open(path, encoding="utf-8-sig") as f:
        return f.read().split("\n")


def bloques_raiz(path):
    """Lista de (nombre, linea_inicio, linea_fin) de bloques de nivel
    raiz. Lineas 1-based, rango inclusivo."""
    if not os.path.exists(path):
        return []
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
                    raices.append((nombre, inicio, n))
            continue
        m = BLOCK_HEADER_RE.match(line)
        if m:
            pila.append((m.group(1), n))
    return raices


def sub_bloque_texto(path, nombre_padre, nombre_sub):
    """Texto del primer bloque `nombre_sub = {` dentro del bloque raiz
    `nombre_padre` de `path`, o None."""
    lineas = leer(path)
    raices = bloques_raiz(path)
    for nombre, inicio, fin in raices:
        if nombre != nombre_padre:
            continue
        texto_padre = "\n".join(lineas[inicio - 1:fin])
        prof = 0
        i = 0
        sub = texto_padre.split("\n")
        for k, raw in enumerate(sub):
            line = strip_comment(raw).strip()
            if not line:
                continue
            m = BLOCK_HEADER_RE.match(line)
            if m and m.group(1) == nombre_sub and prof == 1:
                j = k
                p = 0
                while j < len(sub):
                    s = strip_comment(sub[j]).strip()
                    if s and s != "}":
                        if BLOCK_HEADER_RE.match(s):
                            p += 1
                    elif s == "}":
                        p -= 1
                        if p == 0:
                            break
                    j += 1
                return "\n".join(sub[k:j + 1])
            if m:
                prof += 1
            elif line == "}":
                prof -= 1
        return None
    return None


def regiones_vanilla_terrestres():
    """Set de claves region_* de las 36 regiones terrestres vanilla
    (CORR-3: excluye water_strategic_regions.txt)."""
    regiones = set()
    directorio = os.path.join(V3_GAME, "common", "strategic_regions")
    for nombre in TERRESTRIAL_REGION_FILES:
        path = os.path.join(directorio, nombre)
        if not os.path.exists(path):
            continue
        for linea in leer(path):
            m = re.match(r"^(region_[a-z_]+)\s*=\s*\{", linea)
            if m:
                regiones.add(m.group(1))
    return regiones


def clave_ai_existe_vanilla(claves):
    """M804: verifica que cada clave AI exista en el motor (arbol vanilla
    game/common). Devuelve (presentes, faltantes, arbol_presente)."""
    presentes, faltantes = [], []
    raiz = os.path.join(V3_GAME, "common")
    if not os.path.isdir(raiz):
        return presentes, list(claves), False
    for clave in claves:
        encontrado = False
        for path in glob.glob(os.path.join(raiz, "**", "*.txt"),
                              recursive=True):
            try:
                with open(path, encoding="utf-8-sig",
                          errors="replace") as f:
                    for linea in f:
                        if clave in strip_comment(linea):
                            encontrado = True
                            break
            except OSError:
                continue
            if encontrado:
                break
        if encontrado:
            presentes.append(clave)
        else:
            faltantes.append(clave)
    return presentes, faltantes, True


def main():
    violaciones = []
    avisos = []

    # ---------- Check 1: cantidad de bloques vs regiones vanilla ----------
    regiones_vanilla = regiones_vanilla_terrestres()
    bloques_ai = bloques_raiz(DECISIONS_AI)
    nombres_ai = [n for n, _s, _f in bloques_ai
                  if n.startswith("freraut_ai_admin_region_")]
    if not regiones_vanilla:
        violaciones.append(
            ("check1", "GUARD: 0 regiones terrestres vanilla leidas de %s "
             "(anti-vacuidad M664)" % os.path.join(V3_GAME, "common",
                                                   "strategic_regions")))
    if not nombres_ai:
        violaciones.append(
            ("check1", "GUARD: 0 bloques freraut_ai_admin_region_* en %s "
             "(anti-vacuidad M664)" % DECISIONS_AI))
    else:
        esperadas = {"region_" + n.split("_region_", 1)[1]
                     for n in nombres_ai}
        if regiones_vanilla and esperadas != regiones_vanilla:
            faltan = sorted(regiones_vanilla - esperadas)
            sobran = sorted(esperadas - regiones_vanilla)
            violaciones.append(
                ("check1", "bloques (%d) != regiones vanilla (%d); "
                 "faltan %s; sobran %s" % (len(esperadas),
                                           len(regiones_vanilla),
                                           faltan, sobran)))
        elif regiones_vanilla:
            print("[OK] check1 %d bloques == %d regiones terrestres vanilla"
                  % (len(esperadas), len(regiones_vanilla)))

    # ---------- Checks 2 y 3 sobre las decisiones IA ----------
    if os.path.exists(DECISIONS_AI):
        lineas_ai = leer(DECISIONS_AI)
        for nombre, inicio, fin in bloques_ai:
            if not nombre.startswith("freraut_ai_admin_region_"):
                continue
            texto = "\n".join(lineas_ai[inicio - 1:fin])
            region = nombre.split("_region_", 1)[1]
            etiqueta = "%s:%d" % (DECISIONS_AI, inicio)
            # check 2 esqueleto
            if "is_ai = yes" in texto and "is_subject = no" in texto:
                print("[OK] check2 %s possible is_ai/is_subject" % etiqueta)
            else:
                violaciones.append(
                    (etiqueta, "check2 possible sin is_ai = yes / "
                     "is_subject = no"))
            if "base = 0" in texto:
                adds = [int(m) for m in
                        re.findall(r"^\s*add\s*=\s*(\d+)\s*$", texto,
                                   re.MULTILINE)]
                n_mod = len(re.findall(r"modifier\s*=\s*\{", texto))
                if n_mod >= 4 and adds and max(adds) <= 30 and \
                        sum(adds) <= 82:
                    print("[OK] check2 %s ai_chance base 0, %d modifiers, "
                          "adds %s (techo M803)" % (etiqueta, n_mod, adds))
                else:
                    violaciones.append(
                        (etiqueta, "check2 ai_chance fuera de techo M803 "
                         "(modifiers=%d adds=%s)" % (n_mod, adds)))
            else:
                violaciones.append((etiqueta, "check2 ai_chance sin base = 0"))
            if "NOT = { has_variable = freraut_ai_admin_cooldown }" in texto \
                    and "name = freraut_ai_admin_cooldown" in texto \
                    and "months = 12" in texto:
                print("[OK] check2 %s cooldown M803 (gate + 12 meses)"
                      % etiqueta)
            else:
                violaciones.append(
                    (etiqueta, "check2 cooldown M803 ausente (gate "
                     "has_variable o set_variable months = 12)"))
            if "set_variable = freraut_ai_admin_group" in texto and \
                    "region = sr:region_%s" % region in texto:
                print("[OK] check2 %s when_taken grupo + region sr:region_%s"
                      % (etiqueta, region))
            else:
                violaciones.append(
                    (etiqueta, "check2 when_taken sin set_variable "
                     "freraut_ai_admin_group o sin region = sr:region_%s"
                     % region))
            if "create_dynamic_country" in texto and \
                    "has_variable = freraut_ai_admin_group" in texto:
                print("[OK] check2 %s create_dynamic_country con cede "
                      "has_variable freraut_ai_admin_group" % etiqueta)
            else:
                violaciones.append(
                    (etiqueta, "check2 create_dynamic_country sin "
                     "cede_state_trigger has_variable freraut_ai_admin_group"))

    # ---------- Check 3: on_created del sistema nuevo + jugador ----------
    on_createds = []
    if os.path.exists(DECISIONS_AI):
        lineas_ai = leer(DECISIONS_AI)
        for nombre, inicio, fin in bloques_ai:
            if not nombre.startswith("freraut_ai_admin_region_"):
                continue
            texto = "\n".join(lineas_ai[inicio - 1:fin])
            m = re.search(r"on_created\s*=\s*\{", texto)
            if m:
                on_createds.append(("ai_" + nombre, texto[m.start():]))
    da_texto = leer(DA_FILE) if os.path.exists(DA_FILE) else []
    m = None
    if da_texto:
        for nombre, inicio, fin in bloques_raiz(DA_FILE):
            if nombre == "freraut_da_cease_autonomy":
                texto = "\n".join(da_texto[inicio - 1:fin])
                m = re.search(r"on_created\s*=\s*\{", texto)
                if m:
                    on_createds.append(
                        ("parteb_consolidacion", texto[m.start():]))
                break
    jugador_texto = None
    if os.path.exists(DECISIONS_JUGADOR):
        for nombre, inicio, fin in bloques_raiz(DECISIONS_JUGADOR):
            if nombre == "freraut_approve_autonomy":
                jugador_texto = "\n".join(
                    leer(DECISIONS_JUGADOR)[inicio - 1:fin])
                break

    for etiqueta, texto in on_createds:
        d6_ok = all("has_law = law_type:%s" % ley in texto and
                    "activate_law = law_type:%s" % ley in texto
                    for ley in D6_LAWS)
        orden = [texto.find("activate_law = law_type:%s" % ley)
                 for ley in D6_LAWS]
        d6_orden = all(a >= 0 for a in orden) and orden == sorted(orden)
        if d6_ok and d6_orden:
            print("[OK] check3 %s cadena D6 completa y ordenada" % etiqueta)
        else:
            violaciones.append(
                (etiqueta, "check3 cadena D6 incompleta o desordenada "
                 "(variantes antes del padre)"))
        n_colonial = texto.count(
            "activate_law = law_type:law_colonial_administration")
        if n_colonial == 1:
            print("[OK] check3 %s law_colonial_administration solo en rama "
                  "D6 (excepcion anti-deriva)" % etiqueta)
        else:
            violaciones.append(
                (etiqueta, "check3 activate_law law_colonial_administration "
                 "x%d (esperado 1, solo rama D6)" % n_colonial))
        if all(k in texto for k in EXPLOTACION_KEYS):
            print("[OK] check3 %s rama explotacion anti-deriva (D4)"
                  % etiqueta)
        else:
            faltantes = [k for k in EXPLOTACION_KEYS if k not in texto]
            violaciones.append(
                (etiqueta, "check3 rama explotacion incompleta: %s"
                 % faltantes))
        if all(k in texto for k in COLONIA_KEYS):
            print("[OK] check3 %s rama colonia anti-deriva (D6 sin "
                  "colonial_administration)" % etiqueta)
        else:
            faltantes = [k for k in COLONIA_KEYS if k not in texto]
            violaciones.append(
                (etiqueta, "check3 rama colonia incompleta: %s" % faltantes))
        if BASE_LIBERTY in texto:
            print("[OK] check3 %s freraut_admin_base_liberty" % etiqueta)
        else:
            violaciones.append(
                (etiqueta, "check3 sin freraut_admin_base_liberty"))
        var = ("freraut_ai_admin_group" if etiqueta.startswith("ai_")
               else "freraut_ai_consolidation_group")
        pos_remove = texto.find("remove_variable = %s" % var)
        pos_liberty = texto.find(BASE_LIBERTY)
        if pos_remove > pos_liberty >= 0:
            print("[OK] check3 %s CORR-4 remove_variable %s despues del "
                  "transform" % (etiqueta, var))
        else:
            violaciones.append(
                (etiqueta, "check3 CORR-4 remove_variable %s ausente o "
                 "antes del transform" % var))

    # on_created del jugador: D6 si, Parte C no
    if jugador_texto:
        m_jug = re.search(r"on_created\s*=\s*\{", jugador_texto)
        if m_jug:
            oc_jugador = jugador_texto[m_jug.start():]
            d6_ok = all("has_law = law_type:%s" % ley in oc_jugador and
                        "activate_law = law_type:%s" % ley in oc_jugador
                        for ley in D6_LAWS)
            parte_c = ("activate_law = law_type:law_colonial_exploitation"
                       in oc_jugador or
                       "activate_law = law_type:law_frontier_colonization"
                       in oc_jugador)
            if d6_ok and not parte_c:
                print("[OK] check3 freraut_approve_autonomy D6 presente, "
                      "sin Parte C (flujo del jugador)")
            else:
                violaciones.append(
                    ("freraut_approve_autonomy", "check3 jugador: D6=%s "
                     "ParteC=%s (esperado D6 si, Parte C no)"
                     % (d6_ok, parte_c)))
        else:
            violaciones.append(
                ("freraut_approve_autonomy", "check3 jugador: on_created "
                 "no encontrado"))
    else:
        violaciones.append(
            ("freraut_approve_autonomy", "check3 jugador: bloque no "
             "encontrado en %s" % DECISIONS_JUGADOR))

    # anti-drift: las DAs originales intactas
    if os.path.exists(DA_FILE):
        da = "\n".join(da_texto)
        colonial = sub_bloque_texto(DA_FILE, "freraut_da_colonial_regime",
                                    "accept_effect")
        explot = sub_bloque_texto(DA_FILE, "freraut_da_explotation_regime",
                                  "accept_effect")
        if colonial and "activate_law = law_type:law_colonial_administration" \
                in colonial and "activate_law = law_type:law_frontier_colonization" \
                in colonial:
            print("[OK] check3 DA colonial_regime intacta (D2/D3)")
        else:
            violaciones.append(
                ("freraut_da_colonial_regime", "check3 DA colonial_regime "
                 "modificada o ilegible (D2: NO tocar)"))
        if explot and all(k in explot for k in EXPLOTACION_KEYS):
            print("[OK] check3 DA explotation_regime intacta (D2/D3)")
        else:
            violaciones.append(
                ("freraut_da_explotation_regime", "check3 DA "
                 "explotation_regime modificada o ilegible (D2: NO tocar)"))

    # ---------- Check 4: consolidacion ----------
    if os.path.exists(DA_FILE):
        for nombre, inicio, fin in bloques_raiz(DA_FILE):
            if nombre != "freraut_da_cease_autonomy":
                continue
            # sin comentarios: el propio codigo documenta el reemplazo del
            # tercer gate y el string always = no en comentario es falso
            # positivo
            texto = "\n".join(strip_comment(l)
                              for l in da_texto[inicio - 1:fin])
            if "always = no" not in texto.split("ai = {", 1)[-1]:
                print("[OK] check4 will_propose sin always = no (tercer "
                      "gate abierto)")
            else:
                violaciones.append(
                    ("freraut_da_cease_autonomy", "check4 will_propose "
                     "conserva always = no (tercer gate cerrado)"))
            pos_set = texto.find("set_variable = freraut_ai_consolidation_group")
            pos_annex = texto.find("annex_with_incorporation")
            pos_create = texto.find("create_dynamic_country")
            if 0 <= pos_set < pos_annex < pos_create:
                print("[OK] check4 encadenado D5: marcar -> anexar -> crear")
            else:
                violaciones.append(
                    ("freraut_da_cease_autonomy", "check4 orden D5 roto "
                     "(set=%d annex=%d create=%d)"
                     % (pos_set, pos_annex, pos_create)))
            if "NOT = { any_scope_state = { count >= 3 } }" in texto and \
                    "is_subject_type = subject_type_freraut_administration" \
                    in texto:
                print("[OK] check4 will_propose con condiciones del briefing "
                      "(sujeto <= 2 estados, >= 2 administraciones)")
            else:
                violaciones.append(
                    ("freraut_da_cease_autonomy", "check4 will_propose sin "
                     "las condiciones del briefing"))
            break
    else:
        violaciones.append(("check4", "GUARD: %s no existe" % DA_FILE))

    # ---------- Check 5: NO-REGRESION ----------
    if jugador_texto:
        m_ai = re.search(r"ai_chance\s*=\s*\{\s*base\s*=\s*0",
                         jugador_texto)
        if m_ai:
            print("[OK] check5 freraut_approve_autonomy ai_chance base 0 "
                  "intacto (D2)")
        else:
            violaciones.append(
                ("freraut_approve_autonomy", "check5 ai_chance base 0 "
                 "perdido (D2)"))
    if os.path.exists(DECREES_FILE):
        decrees = leer(DECREES_FILE)
        for esperado in ("freraut_decree_autonomy",
                         "freraut_decree_capital"):
            for nombre, inicio, fin in bloques_raiz(DECREES_FILE):
                if nombre != esperado:
                    continue
                texto = "\n".join(decrees[inicio - 1:fin])
                if re.search(r"ai_weight\s*=\s*\{\s*value\s*=\s*0\s*\}",
                             texto):
                    print("[OK] check5 %s ai_weight value 0 intacto (D2)"
                          % esperado)
                else:
                    violaciones.append(
                        (esperado, "check5 ai_weight value 0 perdido (D2)"))
                break
    else:
        violaciones.append(("check5", "GUARD: %s no existe" % DECREES_FILE))

    # ---------- Check 6 (M804): contenedores de claves AI ----------
    claves_por_contenedor = {
        "decisions": ("ai_chance",),
        "decrees": ("ai_weight",),
        "diplomatic_actions": ("evaluation_chance", "propose_score",
                               "will_propose"),
    }
    prohibidas_por_contenedor = {
        "decisions": ("ai_weight", "evaluation_chance", "propose_score",
                      "will_propose"),
        "decrees": ("ai_chance", "evaluation_chance", "propose_score",
                    "will_propose"),
        "diplomatic_actions": ("ai_chance", "ai_weight"),
    }
    for contenedor, claves in claves_por_contenedor.items():
        dir_mod = os.path.join(ROOT, "common", contenedor)
        archivos = sorted(glob.glob(os.path.join(dir_mod, "freraut_*.txt")))
        if not archivos:
            violaciones.append(
                ("check6", "GUARD: 0 archivos freraut_*.txt en %s" % dir_mod))
            continue
        for path in archivos:
            texto = "\n".join(leer(path))
            for prohibida in prohibidas_por_contenedor[contenedor]:
                if re.search(r"^\s*%s\s*=" % re.escape(prohibida), texto,
                             re.MULTILINE):
                    violaciones.append(
                        ("%s" % path, "check6 M804: %s en contenedor "
                         "equivocado (%s)" % (prohibida, contenedor)))
            for clave in claves:
                if re.search(r"^\s*%s\s*=" % re.escape(clave), texto,
                             re.MULTILINE):
                    print("[OK] check6 %s usa %s en su contenedor valido"
                          % (path, clave))
    presentes, faltantes, arbol = clave_ai_existe_vanilla(
        ["ai_chance", "ai_weight", "evaluation_chance", "propose_score",
         "will_propose"])
    if arbol:
        if faltantes:
            violaciones.append(
                ("check6", "M804: claves sin evidencia en el motor vanilla: "
                 "%s" % faltantes))
        else:
            print("[OK] check6 M804 claves AI existen en el motor vanilla: "
                  "%s" % presentes)
    else:
        avisos.append("check6 M804: arbol vanilla no disponible en %s; "
                      "existencia de claves no verificada" % V3_GAME)

    for aviso in avisos:
        print("AVISO (no violacion): %s" % aviso)
    for etiqueta, mensaje in violaciones:
        print("VIOLACION %s: %s" % (etiqueta, mensaje))
    print("bloques AI: %d, regiones vanilla: %d, violaciones: %d"
          % (len(nombres_ai), len(regiones_vanilla), len(violaciones)))
    return 1 if violaciones else 0


if __name__ == "__main__":
    sys.exit(main())
