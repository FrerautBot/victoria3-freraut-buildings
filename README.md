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

- `state_construction_add` está registrada como modifier type propio del mod (`common/modifier_type_definitions/freraut_modifier_types.txt`). Su efecto en runtime (bonus de construcción de Public Works) está pendiente de verificación en una partida.

## Cómo verificar tu instalación

1. Iniciá Victoria 3 con el mod activo.
2. Verificá que el juego no reporte errores del mod en:

   ```
   C:\Users\lucas\Documents\Paradox Interactive\Victoria 3\logs\error.log
   ```

3. En una partida, buscá los edificios del mod (por ejemplo, el Mining Center) y confirmá que sus métodos de producción aparecen correctamente.

## Distribución

Este mod se distribuye por dos canales: backup manual en este repositorio público de GitHub y Steam Workshop.
