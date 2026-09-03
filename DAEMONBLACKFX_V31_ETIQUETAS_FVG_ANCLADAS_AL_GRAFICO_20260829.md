# DaemonBlackFx v31 — Etiquetas FVG ancladas al gráfico

## Objetivo
Corregir la sensación de que las etiquetas FVG permanecían pegadas al viewport al navegar el gráfico.

## Cambio principal
Las zonas FVG/OB y sus etiquetas ahora comparten la misma coordenada temporal global basada en la vela de origen. El renderer convierte esa coordenada global a la ventana visible usando `chartObjectX(...)`.

Se eliminó el clamp visual que forzaba la etiqueta a permanecer dentro del borde derecho/superior. Si la vela de origen se desplaza, la etiqueta se desplaza con ella; si sale del viewport, la etiqueta también sale del viewport.

## Clipping
Zona y etiqueta se renderizan dentro de `chartPriceClip`, de modo que no invaden los ejes cuando quedan fuera del área de precios.

## Alcance
Cambio exclusivo del dashboard. No modifica reglas SMC, confirmaciones, riesgo, ejecución, Break Even ni gestión de posiciones.
