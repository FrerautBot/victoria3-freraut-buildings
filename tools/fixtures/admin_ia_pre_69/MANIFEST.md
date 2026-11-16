# Fixture admin_ia_pre_69 (M777, task-72 Parte D)

Estado ANTES de orden-69 (copia de HEAD 94924bd via `git show HEAD:`).
Archivos: common/decisions/freraut_autonomy_decisions.txt,
common/diplomatic_actions/freraut_administration_actions.txt y
common/decrees/freraut_autonomy_decrees.txt (los 3 que lee
validar_admin_ia.py ademas de freraut_ai_admin_decisions.txt).

DELIBERADO: freraut_ai_admin_decisions.txt NO se incluye — el check 1
debe disparar su guard anti-vacuidad (0 bloques freraut_ai_admin_region_*)
y el check 3 no debe encontrar on_created del sistema nuevo.

## Violaciones esperadas (salida del red test registrada)

Salida registrada del validador: `violaciones: 5`, exit 1.

1. Check 1: GUARD 0 bloques freraut_ai_admin_region_* en
   common/decisions/freraut_ai_admin_decisions.txt (archivo ausente,
   anti-vacuidad M664).
2. Check 3 jugador: freraut_approve_autonomy sin cadena D6
   (D6=False ParteC=False; esperado D6 si, Parte C no).
3. Check 4: will_propose de freraut_da_cease_autonomy conserva
   `always = no` (tercer gate cerrado, ADENDA).
4. Check 4: orden D5 roto — accept_effect sin set_variable
   freraut_ai_consolidation_group antes del annex y sin
   create_dynamic_country despues (set=-1 create=-1).
5. Check 4: will_propose sin las condiciones del briefing
   (NOT any_scope_state count >= 3 ausente).
