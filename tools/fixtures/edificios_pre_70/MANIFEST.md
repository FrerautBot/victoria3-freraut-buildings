# Fixture edificios_pre_70 (M777)

Estado ANTES de task-70 (copia del working tree al Paso 0, HEAD e0cdb00).
Archivos: common/buildings/freraut_buildings.txt,
common/production_methods/freraut_pms.txt,
common/production_method_groups/freraut_pmgs.txt,
common/building_groups/freraut_building_groups.txt y
common/modifier_type_definitions/freraut_modifier_types.txt (los 5 que lee
validar_edificios.py; el 4to se agrego tras el hallazgo M687 y el 5to tras
el hallazgo de tipos sin definicion, ver abajo).

## Violaciones esperadas (salida del red test registrada)

Salida registrada del validador: `violaciones: 28`, exit 1
(24 tras task-70 + 4 nuevas del fix palacio 2026-11-15, checks 1b/1c).

1. Check 1a: palacio sin bloque `possible` (falta `is_capital = yes`).
2-4. Check 1b (fix palacio 2026-11-15: el menu de construccion
    gubernamental filtra por can_build_government, NO por possible):
    can_build_government del palacio sin `is_capital = yes`, sin
    `is_incorporated = yes` y sin `country_has_building_type_levels`
    (unicidad). Precedentes vanilla: skyscraper 07_government.txt:186,
    11_private_infrastructure.txt:275.
5. Check 1c: palacio sin `expandable = no` (1 nivel, precedente skyscraper
   07_government.txt:173).
6. Check 2: pm_sovereign_palace_base sin state_modifiers (falta
   `building_sovereign_palace_throughput_add = 0.10`).
7. Check 2 (B.2): la clave de throughput aparece 0 veces (esperado 1).
8. Check 2 (tipo): falta definicion de tipo para
   building_sovereign_palace_throughput_add en
   freraut_modifier_types.txt (patron vanilla
   01_building_modifier_types.txt:2642).
9. Check 3: bg_sovereign_palace con `urbanization = 20` (se exige 40;
   doctrina M687: la urbanizacion per-level es el campo `urbanization`
   del building group, no state_urbanization_per_level_add en el PM).
10-21. Check 4: 12 edificios sin `possible` con `is_incorporated = yes`
    (central_bank, mining_center, public_works, sovereign_palace,
    tech_university, national_trade, logistics_center, national_academy,
    stock_exchange, fertilization_center, breeding_center,
    grand_company_bank).
22. Check 4: dissident_agency con possible sin `is_incorporated = yes`.
23. Check 5: headers activos de manufactura/trenes en lineas 85 y 341
    (deben estar comentados).
24. Check 5: bloques no encontrados comentados (manufactura y trenes).
25. Check 6: pmg_sovereign_palace_flats no existe.
26. Check 6: production_method_groups del palacio sin
    pmg_sovereign_palace_flats.
27. Check 6 (tipo): falta definicion de tipo para goods_input_furniture_add
    en freraut_modifier_types.txt (clave custom, no existe en vanilla).
28. Check 6: pm_sovereign_palace_flats no existe.

Nota: check 4 negativo (public_health sin is_incorporated) ya pasa en
este estado pre-task — es un check de no-regresion.

El fixture debe seguir en rojo (exit != 0) para siempre: es el baseline
pre-70 del meta-test de edificios.
