# DaemonBlackFx v14 · Auditoría visual de la entrada

## Objetivo

El dashboard de posiciones abiertas ahora puede reconstruir visualmente **por qué se abrió una operación** y comparar esa tesis original contra **lo que la estrategia ve ahora**.

La interfaz sigue siendo de auditoría: no abre, modifica ni cierra operaciones.

## Capas activables del gráfico

- Trade / SL / TP / Break Even.
- CHOCH / BOS.
- Liquidez / sweeps.
- Order Blocks.
- Confluencias: divergencia RSI, Doji H1 en extremo y patrón armónico.
- RSI 14.

Cada capa puede activarse o desactivarse sin afectar al daemon.

## Tesis al abrir vs. estado actual

Para cada posición se publican dos snapshots diferentes:

1. **Tesis al abrir**: datos persistidos en SQLite al momento de ejecutar el trade. No se sobrescriben con análisis posteriores.
2. **Lo que ve ahora**: último análisis del mismo instrumento.

Se comparan dirección, score, porcentaje de confirmaciones, tendencia H1, estructura, zona Premium/Discount, confirmaciones cumplidas/faltantes, divergencia, Doji H1 y armónico.

## RSI 14

El snapshot M5 incorpora RSI 14 calculado con suavizado tipo Wilder mediante EWM. Se usa exclusivamente como evidencia visual para poder auditar divergencias; el dashboard no recalcula decisiones de trading.

## Momento de entrada

El gráfico dibuja una línea vertical sobre la vela M5 más cercana al `entry_time` y muestra el score y porcentaje de confirmaciones originales. Si la entrada tuvo divergencia, Doji H1 o armónico, aparecen etiquetas junto al momento de entrada.

## Seguridad

- El navegador no consulta MT5 directamente.
- Las velas y snapshots se generan en el mismo hilo cooperativo del daemon.
- Las capas sólo modifican la visualización local.
- El monitor continúa siendo asesor: `MANTENER`, `VIGILAR`, `PROTEGER`, `SALIDA A EVALUAR`.
