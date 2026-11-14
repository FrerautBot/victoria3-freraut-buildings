# Freraut Buildings

Mod para Victoria 3 que agrega **16 edificios custom** con métodos de producción ajustados, incluyendo producción de cobre en el Mining Center y un bonus de construcción en Public Works.

## Contenido

- **16 edificios custom** con métodos de producción propios.
- **Bien custom** `corporate_financial_services` (servicios financieros corporativos), consumido y producido por los edificios del mod.
- **Países confederados** con decisiones propias, incluyendo caminos ideológicos (`freraut_ideological_paths`).
- **Eventos** de confederación, ideológicos y de unificación.
- **Power blocs** con identidades y principios propios.

## Requisitos

- Victoria 3 versión soportada: **1.15.\***
- ID del mod: `com.freraut.buildings`

## Instalación

### Vía Steam Workshop

1. Suscribite al mod "Freraut Buildings" en el Steam Workshop.
2. Activalo en el Launcher de Paradox dentro de la lista de reproducción activa.

### Instalación manual

1. Descargá la carpeta del mod desde este repositorio.
2. Copiá la carpeta completa `Freraut Buildings` a:

   ```
   Documents\Paradox Interactive\Victoria 3\mod\
   ```

3. Activá el mod en el Launcher de Paradox.

## Limitaciones conocidas

- Obras Públicas otorga sus bonus de construcción con claves vanilla verificadas: `state_construction_mult = 0.05` (+5% de eficiencia de construcción en el estado) y `country_construction_add = 10` (+10 de construcción por semana). Ya no depende de un modifier type custom sin evidencia en runtime.
- Acción "Establecer régimen tributario" (orden-62): la DA `freraut_da_set_tribute` aplica solo a súbditos "Administración" y abre un evento de selección con escalones discretos de tributo 10/20/30/40/50/60/70/80 % (pactos ocultos `freraut_da_tribute_p*`). El 20 % es el pacto original `freraut_da_tribute`; el régimen de explotación restablece el 20 % al aplicarse.
- Orden-63: se corrigió la dirección del tributo (el vasallo paga al señor; antes estaba invertida), se agregó la opción "Exención (0%)" y la acción "Invertir en desarrollo" (`freraut_da_dev_invest`) para Administraciones y títeres vanilla, con escalones 10-80 % pagados por el señor. Nota de migración: en partidas ya guardadas los pactos viejos conservan la dirección invertida hasta re-ejecutar la acción sobre el mismo sujeto.
- Orden-64: nueva acción "Establecer aporte de la unión" (`freraut_da_union_tribute`) para Estados Confederados: un único escalón 10-80 % aplicado a TODOS los confederados del señor (reutiliza los pactos ocultos `freraut_da_tribute_*`), con exención 0 % union-wide. Además terminó la exclusión mutua tributo/desarrollo: ambos pactos pueden coexistir sobre el mismo súbdito y el neto se suma/resta por diferencia de flujos (el confederado paga el tributo al señor; el señor paga el desarrollo al súbdito).

## Cómo verificar tu instalación

1. Iniciá Victoria 3 con el mod activo.
2. Verificá que el juego no reporte errores del mod en:

   ```
   <Usuario>\Documents\Paradox Interactive\Victoria 3\logs\error.log
   ```

3. En una partida, buscá los edificios del mod (por ejemplo, el Mining Center) y confirmá que sus métodos de producción aparecen correctamente.

## Distribución

Este mod se distribuye por dos canales: backup manual en este repositorio público de GitHub y Steam Workshop.

## Balance declarado (orden-58)

Balance /4 aplicado en commit `b608ada` (orden-58): outputs y empleo ÷4, inputs/construcción/techs intactos, oro del banco 25/15. Baseline jugable = `b608ada`. Verificación de monotonía con `python tools/validar_balance.py`.

## Tabla de países para la prueba de la rama corona (orden-61)

El evento `freraut_confederation.5` (events/freraut_confederation_events.txt:134-137) evalúa la LEY inicial de gobierno (`has_law_or_variant = law_type:law_monarchy` o `law_type:law_theocracy`). Países vanilla grandes válidos para probar la rama corona:

| País | Archivo history | Línea | Ley inicial | ¿Activa rama corona? |
|---|---|---|---|---|
| Rusia | rus - russia.txt | :12 | law_monarchy | Sí |
| Austria | aus - austria.txt | :12 | law_monarchy | Sí |
| Imperio Otomano | tur - ottoman empire.txt | :16 | law_monarchy | Sí |
| Japón | jap - japan.txt | :14 | law_monarchy | Sí |
| España | spa - spain.txt | :29 | law_monarchy | Sí |
| Estados Pontificios | pap - papal states.txt | :12 | law_theocracy | Sí |

Todo país fresco vanilla cumple además `NOT has_variable freraut_ideology_chosen` (la variable solo la setean las decisiones del mod).

## Verificación runtime pendiente

Errores preexistentes del `error.log` NO son del mod nuevo (firma binaria de la sesión 2026-11-13 19:05): 7 `Unknown modifier type: goods_input_` + 41 `Duplicated key ideology_`. Recontar tras la próxima sesión de juego y comparar contra esa base. Verificación estructural de else/else_if con `python tools/validar_else.py` (62 bloques OK en el árbol vigente).
