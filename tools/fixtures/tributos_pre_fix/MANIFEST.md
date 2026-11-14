# Fixture tributos_pre_fix (M750)

Estado ANTES de task-67 (commit `3c959dc^`, orden-65 8f6a55a). Archivos
extraidos con `git show 3c959dc^:<path>`:

- common/on_actions/freraut_on_actions.txt
- common/diplomatic_actions/freraut_administration_actions.txt
- events/freraut_union_events.txt
- events/freraut_tribute_events.txt

## Violaciones esperadas (red test original de task-67 + clases 67b)

Salida registrada del validador: `violaciones: 20`, exit 1.

1. GUARD anti-vacuidad M664: `freraut_tribute_monthly_pulse` no definido
   (el pulso lo creo task-67; equivalente a "pulso sin NOT exempt" del red
   test original). Impreso, no contado en el total.
2-9. Parte A: los 8 pactos de tributo con `relations_progress_per_day`
   (8 violaciones).
10. Parte C: `add_loyalists 0.02 x8` ausentes en freraut_tribute_events.txt
    (encontrados []).
11. Parte D: falta `set_variable freraut_union_exempt value = 1` en la
    opcion d de freraut_union.1.
12-19. M747 (clase 67b): las 8 opciones de freraut_union.2/.3 con
    `create_diplomatic_pact` sin `remove_variable freraut_union_exempt`.
20. M747: conteo total `remove_variable freraut_union_exempt` = 0
    (esperado 8).
21. M749 (clase 67b): accept_effect del regimen sin `add_loyalists 0.02`.

El fixture debe seguir en rojo (exit != 0) para siempre: es el baseline
pre-fix del meta-test.
