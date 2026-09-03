# DaemonBlackFx v19 — Auditoría visual SMC ampliada

Esta versión amplía exclusivamente la visualización de posiciones abiertas. No cambia la lógica de entrada, el umbral adaptativo mínimo del 80%, el sizing, Break Even ni la ejecución.

## Capas activables del gráfico

- Trade / Entrada / SL / TP / Break Even
- Swings y estructura: HH, HL, LH, LL
- CHOCH y BOS
- Buy-Side Liquidity (BSL), Sell-Side Liquidity (SSL) y sweeps
- Order Blocks completos, con estado visual FRESCA / MITIGADA / INVALIDADA
- Premium, Discount y Equilibrium 50%
- Fair Value Gaps / Imbalances, con estado ABIERTA / MITIGADA_PARCIAL / RELLENADA
- Divergencia RSI, Doji H1 y patrón armónico cuando fueron registrados
- RSI 14

## Multi-timeframe

El panel lateral publica contexto SMC de H1, M15 y M5 usando la caché del mismo MultiTimeframeAnalyzer. El navegador no consulta MetaTrader5.

## Importante sobre FVG

Los FVG se presentan como **contexto SMC auxiliar**. En v19 no son una confirmación obligatoria ni modifican el score/porcentaje de entrada. Esto evita cambiar retrospectivamente la estrategia sólo por añadir una capa al gráfico.

## Seguridad

La generación del snapshot se hace en el mismo hilo cooperativo del daemon. El dashboard sólo consume JSON y dibuja la evidencia; no abre, modifica ni cierra operaciones.
