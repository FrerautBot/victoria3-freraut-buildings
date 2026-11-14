# Fixture tributos_pre_67b (M750)

Estado ANTES de task-67b (copia del working tree al Paso 0, HEAD 64d9461).
Mismos 4 archivos que tributos_pre_fix.

## Violaciones esperadas (las 3 clases nuevas de task-67b)

Salida registrada del validador: `violaciones: 14`, exit 1.

1. B.2: `change_relations` con valores [-9, -4, -2, 4] != esperados
   [-9, -4, -2, 4, 13] (falta la rama +13 de la banda 0%, M748).
2-9. M747: las 8 opciones de freraut_union.2/.3 con create_diplomatic_pact
    sin `remove_variable freraut_union_exempt`.
10. M747: conteo total remove_variable = 0 (esperado 8).
11. M748-a: trigger del pulso sin `has_variable freraut_union_exempt` en el
    OR de any_subject_or_below.
12. M748-b: limit del loop confederado sin `has_variable
    freraut_union_exempt` en el OR.
13. M748-c: falta rama `if` con limit has_variable y `change_relations
    value = 13`.
14. M749: accept_effect de freraut_da_explotation_regime sin
    `add_loyalists 0.02` en scope:target_country.

El fixture debe seguir en rojo (exit != 0) para siempre: es el baseline
pre-67b del meta-test.
