# DaemonBlackFx v29 — Entrada vs. Ahora debajo del gráfico

## Objetivo
Mejorar la legibilidad del visor de auditoría SMC de posiciones abiertas.

## Cambio principal
El bloque **Entrada vs. Ahora** deja de ocupar una columna lateral y pasa a mostrarse **debajo del gráfico**.

El visor queda organizado así:

1. Capas SMC y leyenda.
2. Gráfico interactivo a todo el ancho disponible.
3. Bloque Entrada vs. Ahora debajo del gráfico.
   - Tesis al abrir.
   - Lo que ve ahora.
   - Recomendación y salud.
   - Mapa SMC de la temporalidad seleccionada.
   - Contexto multi-timeframe.
   - Razones de salud.

## Beneficios
- Más ancho útil para velas y estructuras SMC.
- Mejor lectura de Order Blocks, FVG, CHOCH/BOS, liquidez y niveles de trade.
- La comparación de entrada no desaparece; queda justo debajo del gráfico.
- El modo pantalla completa continúa afectando únicamente al gráfico.
- Se mantiene la navegación M1/M5/M15/H1 y el scroll/zoom vertical de v28.

## Estrategia
No se modificaron reglas de trading, scoring, confirmaciones, riesgo, TP1/RUNNER ni Break Even.

## Validación
- 18 pruebas específicas del dashboard aprobadas.
- 197 pruebas no-MT5 aprobadas.
