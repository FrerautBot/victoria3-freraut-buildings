# -*- coding: utf-8 -*-
"""Generador determinista de common/decisions/freraut_ai_admin_decisions.txt
(orden-69, task-72 Parte A): un bloque freraut_ai_admin_region_<REGION> por
cada region estrategica terrestre vanilla (36, CORR-3). Se guarda junto a los
validadores para regenerar el archivo sin drift de transcripcion manual.

Uso:  python tools/gen_admin_ia_decisions.py
"""
import io
import os

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

REGIONES = [
    "andes", "arabia", "atlantic_coast", "balkans", "brazil", "canada",
    "central_america", "central_asia", "central_europe", "east_africa",
    "eastern_europe", "equatorial_africa", "gran_colombia", "great_plains",
    "greater_persia", "himalayas", "indochina", "indonesia", "la_plata",
    "near_east", "nile_basin", "north_africa", "north_china", "north_india",
    "northeast_asia", "northern_europe", "oceania", "pacific_coast", "russia",
    "siberia", "south_china", "south_india", "southern_africa",
    "southern_europe", "west_africa", "western_europe",
]

CABECERA = """############################################
# Decisiones IA de administraciones automaticas (orden-69, task-72)
# Una decision por region estrategica terrestre (36, CORR-3): la IA crea
# una Administracion freraut agrupando los estados que posee en la region.
# - CORR-1: no existe campo `hidden` en 1.15 (0 usos vanilla); el gate es
#   is_ai = yes en possible (precedente is_ai = no en decisiones de
#   expedicion vanilla) + ai_chance base 0.
# - M803 anti-spam: cooldown global de 12 meses por pais
#   (set_variable con months + gate has_variable, patron vanilla
#   00_colonial_administration_buttons.txt:34/:91-94) y techo explicito del
#   ai_chance: base 0 + modifiers acotados (max 2+10+20+30+15+5 = 82).
# - D4 (confirmada por Lucas): explotacion si la region tiene oro, petroleo,
#   caucho, carbon o hierro (CORR-2: has_potential_resource = building_X,
#   ancla 00_companies_americas.txt:129); si no, colonia.
# - D6: herencia de la forma de gobierno del senor (cadena de 9 leyes de
#   lawgroup_governance_principles, variantes antes del padre; la rama
#   colonia NO activa law_colonial_administration inline para no pisar la
#   herencia — excepcion documentada al anti-deriva contra la DA).
# - CORR-4: higiene remove_variable en on_created (patron vanilla
#   00_colonial_administration_buttons.txt:95-97).
# - possible exige >= 1 estado cedible (region sin is_capital) para evitar
#   create_dynamic_country con capital nulo.
############################################

"""


def cadena_d6(overlord):
    leyes = [
        "law_social_monarchy", "law_presidential_republic",
        "law_parliamentary_republic", "law_theocracy", "law_council_republic",
        "law_corporate_state", "law_chiefdom", "law_colonial_administration",
        "law_monarchy",
    ]
    out = []
    for i, ley in enumerate(leyes):
        kw = "if" if i == 0 else "else_if"
        out.append("\t\t\t\t%s = {" % kw)
        out.append("\t\t\t\t\tlimit = {")
        out.append("\t\t\t\t\t\tscope:%s = {" % overlord)
        out.append("\t\t\t\t\t\t\thas_law = law_type:%s" % ley)
        out.append("\t\t\t\t\t\t}")
        out.append("\t\t\t\t\t}")
        out.append("\t\t\t\t\tactivate_law = law_type:%s" % ley)
        out.append("\t\t\t\t}")
    return "\n".join(out)


def bloque(region):
    return """freraut_ai_admin_region_{reg} = {{
\t# Administracion IA en la region estrategica {reg} (orden-69).

\tpossible = {{
\t\tis_ai = yes
\t\tis_subject = no
\t\tis_at_war = no
\t\tNOT = {{ has_variable = freraut_ai_admin_cooldown }}
\t\tany_scope_state = {{
\t\t\tcount >= 1
\t\t\tregion = sr:region_{reg}
\t\t\tNOT = {{ is_capital = yes }}
\t\t}}
\t}}

\tai_chance = {{
\t\tbase = 0
\t\tmodifier = {{
\t\t\tadd = 2
\t\t\tany_scope_state = {{
\t\t\t\tcount >= 1
\t\t\t\tregion = sr:region_{reg}
\t\t\t}}
\t\t}}
\t\tmodifier = {{
\t\t\tadd = 10
\t\t\tany_scope_state = {{
\t\t\t\tcount >= 2
\t\t\t\tregion = sr:region_{reg}
\t\t\t}}
\t\t}}
\t\tmodifier = {{
\t\t\tadd = 20
\t\t\tany_scope_state = {{
\t\t\t\tcount >= 3
\t\t\t\tregion = sr:region_{reg}
\t\t\t}}
\t\t}}
\t\tmodifier = {{
\t\t\tadd = 30
\t\t\tany_scope_state = {{
\t\t\t\tcount >= 4
\t\t\t\tregion = sr:region_{reg}
\t\t\t}}
\t\t}}
\t\tmodifier = {{
\t\t\tadd = 15
\t\t\tany_scope_state = {{
\t\t\t\tregion = sr:region_{reg}
\t\t\t\tany_scope_pop = {{
\t\t\t\t\tpop_acceptance < acceptance_status_4
\t\t\t\t}}
\t\t\t}}
\t\t}}
\t\tmodifier = {{
\t\t\tadd = 5
\t\t\tNOT = {{
\t\t\t\tcapital = {{
\t\t\t\t\tregion = sr:region_{reg}
\t\t\t\t}}
\t\t\t}}
\t\t}}
\t}}

\twhen_taken = {{
\t\tset_variable = {{
\t\t\tname = freraut_ai_admin_cooldown
\t\t\tmonths = 12
\t\t}}
\t\tsave_scope_as = freraut_ai_overlord
\t\tevery_scope_state = {{
\t\t\tlimit = {{
\t\t\t\tregion = sr:region_{reg}
\t\t\t}}
\t\t\tset_variable = freraut_ai_admin_group
\t\t}}
\t\trandom_scope_state = {{
\t\t\tlimit = {{
\t\t\t\tregion = sr:region_{reg}
\t\t\t\towner = scope:freraut_ai_overlord
\t\t\t\tNOT = {{ is_capital = yes }}
\t\t\t}}
\t\t\tsave_scope_as = freraut_ai_admin_capital
\t\t}}
\t\tordered_primary_culture = {{
\t\t\torder_by = "root.culture_percent_country(this)"
\t\t\tposition = 0
\t\t\tsave_scope_as = freraut_admin_culture_1
\t\t}}
\t\tif = {{
\t\t\tlimit = {{
\t\t\t\tany_primary_culture = {{
\t\t\t\t\tcount >= 2
\t\t\t\t}}
\t\t\t}}
\t\t\tordered_primary_culture = {{
\t\t\t\torder_by = "root.culture_percent_country(this)"
\t\t\t\tposition = 1
\t\t\t\tsave_scope_as = freraut_admin_culture_2
\t\t\t}}
\t\t}}
\t\tif = {{
\t\t\tlimit = {{
\t\t\t\tany_primary_culture = {{
\t\t\t\t\tcount >= 3
\t\t\t\t}}
\t\t\t}}
\t\t\tordered_primary_culture = {{
\t\t\t\torder_by = "root.culture_percent_country(this)"
\t\t\t\tposition = 2
\t\t\t\tsave_scope_as = freraut_admin_culture_3
\t\t\t}}
\t\t}}
\t\tcreate_dynamic_country = {{
\t\t\torigin = root
\t\t\tcountry_type = colonial
\t\t\ttier = principality
\t\t\tculture = scope:freraut_admin_culture_1
\t\t\tcapital = scope:freraut_ai_admin_capital
\t\t\tcede_state_trigger = {{
\t\t\t\thas_variable = freraut_ai_admin_group
\t\t\t\tNOT = {{ is_capital = yes }}
\t\t\t}}
\t\t\ton_created = {{
\t\t\t\tset_variable = freraut_admin_var
\t\t\t\tif = {{
\t\t\t\t\tlimit = {{
\t\t\t\t\t\texists = scope:freraut_admin_culture_2
\t\t\t\t\t}}
\t\t\t\t\tadd_primary_culture = scope:freraut_admin_culture_2
\t\t\t\t}}
\t\t\t\tif = {{
\t\t\t\t\tlimit = {{
\t\t\t\t\t\texists = scope:freraut_admin_culture_3
\t\t\t\t\t}}
\t\t\t\t\tadd_primary_culture = scope:freraut_admin_culture_3
\t\t\t\t}}
\t\t\t\t# D6: herencia de la forma de gobierno del senor (variantes
\t\t\t\t# especificas antes del padre; has_law/activate_law anclados en
\t\t\t\t# 00_colonial_administration_buttons.txt:98-99).
{d6}
\t\t\t\t# Parte C: transformacion inline colonia/explotacion (D4).
\t\t\t\tif = {{
\t\t\t\t\tlimit = {{
\t\t\t\t\t\tany_scope_state = {{
\t\t\t\t\t\t\tOR = {{
\t\t\t\t\t\t\t\thas_potential_resource = building_gold_mine
\t\t\t\t\t\t\t\thas_potential_resource = building_gold_field
\t\t\t\t\t\t\t\thas_potential_resource = building_oil_rig
\t\t\t\t\t\t\t\thas_potential_resource = building_rubber_plantation
\t\t\t\t\t\t\t\thas_potential_resource = building_coal_mine
\t\t\t\t\t\t\t\thas_potential_resource = building_iron_mine
\t\t\t\t\t\t\t}}
\t\t\t\t\t\t}}
\t\t\t\t\t}}
\t\t\t\t\t# rama explotacion (espejo freraut_da_explotation_regime
\t\t\t\t\t# :701-713; anti-deriva M797)
\t\t\t\t\tactivate_law = law_type:law_colonial_exploitation
\t\t\t\t\tadd_modifier = {{
\t\t\t\t\t\tname = freraut_admin_exploitation
\t\t\t\t\t}}
\t\t\t\t\tfreraut_remove_all_tribute_pacts = yes
\t\t\t\t\tcreate_diplomatic_pact = {{
\t\t\t\t\t\tcountry = scope:freraut_ai_overlord
\t\t\t\t\t\ttype = freraut_da_tribute
\t\t\t\t\t}}
\t\t\t\t\tadd_loyalists = {{
\t\t\t\t\t\tvalue = 0.02
\t\t\t\t\t}}
\t\t\t\t}}
\t\t\t\telse = {{
\t\t\t\t\t# rama colonia (espejo freraut_da_colonial_regime :634-654
\t\t\t\t\t# sin la activacion de law_colonial_administration: D6)
\t\t\t\t\tscope:freraut_ai_overlord = {{
\t\t\t\t\t\tevery_primary_culture = {{
\t\t\t\t\t\t\tlimit = {{
\t\t\t\t\t\t\t\tNOT = {{ is_primary_culture_of = root }}
\t\t\t\t\t\t\t}}
\t\t\t\t\t\t\tsave_temporary_scope_as = freraut_admin_temp_culture
\t\t\t\t\t\t\troot = {{
\t\t\t\t\t\t\t\tadd_primary_culture = scope:freraut_admin_temp_culture
\t\t\t\t\t\t\t}}
\t\t\t\t\t\t}}
\t\t\t\t\t}}
\t\t\t\t\tactivate_law = law_type:law_frontier_colonization
\t\t\t\t\tfreraut_remove_all_tribute_pacts = yes
\t\t\t\t}}
\t\t\t\tadd_modifier = {{
\t\t\t\t\tname = freraut_admin_base_liberty
\t\t\t\t}}
\t\t\t\t# CORR-4: higiene de variables (patron vanilla
\t\t\t\t# 00_colonial_administration_buttons.txt:95-97)
\t\t\t\tevery_scope_state = {{
\t\t\t\t\tremove_variable = freraut_ai_admin_group
\t\t\t\t}}
\t\t\t}}
\t\t}}
\t\thidden_effect = {{
\t\t\tcreate_diplomatic_pact = {{
\t\t\t\tcountry = scope:freraut_ai_admin_capital.owner
\t\t\t\ttype = freraut_da_create_administration
\t\t\t}}
\t\t}}
\t}}
}}
""".format(reg=region, d6=cadena_d6("freraut_ai_overlord"))


def main():
    destino = os.path.join(BASE, "common", "decisions",
                           "freraut_ai_admin_decisions.txt")
    with io.open(destino, "w", encoding="utf-8", newline="\n") as f:
        f.write(CABECERA)
        for i, reg in enumerate(REGIONES):
            f.write(bloque(reg))
            if i < len(REGIONES) - 1:
                f.write("\n")
    print("bloques escritos: %d -> %s" % (len(REGIONES), destino))


if __name__ == "__main__":
    main()
