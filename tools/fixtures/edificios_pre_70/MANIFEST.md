# Fixture edificios_pre_70 (M777)

Estado ANTES de task-70 (copia del working tree al Paso 0, HEAD e0cdb00).
Archivos: common/buildings/freraut_buildings.txt,
common/production_methods/freraut_pms.txt,
common/production_method_groups/freraut_pmgs.txt y
common/building_groups/freraut_building_groups.txt (los 4 que lee
validar_edificios.py; el 4to se agrego tras el hallazgo M687, ver abajo).

## Violaciones esperadas (salida del red test registrada)

Salida registrada del validador: `violaciones: 22`, exit 1.

1. Check 1: palacio sin bloque `possible` (falta `is_capital = yes`).
2. Check 2: pm_sovereign_palace_base sin state_modifiers (falta
   `building_sovereign_palace_throughput_add = 0.10`).
3. Check 2 (B.2): la clave de throughput aparece 0 veces (esperado 1).
4. Check 3: bg_sovereign_palace con `urbanization = 20` (se exige 40;
   doctrina M687: la urbanizacion per-level es el campo `urbanization`
   del building group, no state_urbanization_per_level_add en el PM).
5-16. Check 4: 12 edificios sin `possible` con `is_incorporated = yes`
    (central_bank, mining_center, public_works, sovereign_palace,
    tech_university, national_trade, logistics_center, national_academy,
    stock_exchange, fertilization_center, breeding_center,
    grand_company_bank).
17. Check 4: dissident_agency con possible sin `is_incorporated = yes`.
18. Check 5: headers activos de manufactura/trenes en lineas 85 y 341
    (deben estar comentados).
19. Check 5: bloques no encontrados comentados (manufactura y trenes).
20. Check 6: pmg_sovereign_palace_flats no existe.
21. Check 6: production_method_groups del palacio sin
    pmg_sovereign_palace_flats.
22. Check 6: pm_sovereign_palace_flats no existe.

Nota: check 4 negativo (public_health sin is_incorporated) ya pasa en
este estado pre-task — es un check de no-regresion.

El fixture debe seguir en rojo (exit != 0) para siempre: es el baseline
pre-70 del meta-test de edificios.
