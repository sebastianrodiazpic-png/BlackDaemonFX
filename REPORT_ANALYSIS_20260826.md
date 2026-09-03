# Análisis del reporte DEMO 2026-08-26

Fuente analizada: `deriv_demo_trading_report.xlsx`.

## Resumen del reporte

- Total de operaciones: 10
- Cerradas: 8
- Abiertas al momento de exportar: 2
- Ganadoras registradas: 0
- Perdedoras registradas: 6
- Break Even registrados: 0
- Pérdida bruta reportada: 590.30

## Observación sobre Break Even

El reporte no contiene la excursión máxima intratrade ni una serie de precios por
posición, por lo que el XLSX por sí solo no permite demostrar con certeza cuáles
operaciones alcanzaron 1R antes de cerrar.

Sí permite observar que no se registró ningún Break Even.

El código fuente confirma que la lógica de Break Even existía para PAPER y
PositionManager, pero el `demo-daemon` no ejecutaba el monitoreo real de las
posiciones abiertas ni modificaba el Stop Loss de MT5.

Esta es la razón funcional que se corrigió.

## Operaciones cerradas con pérdida cercana al riesgo objetivo

Las operaciones 3 a 9 cerradas por `mt5_history_sync` muestran pérdidas netas
aproximadamente entre 94.67 y 101.66, coherentes con una intención de riesgo de
aproximadamente 1% sobre una cuenta cercana a 10,000.

## Caso Volatility 75 Index

Datos registrados:

- Entry: 50152.99
- SL: 49881.60
- TP: 50695.77
- Volume: 15.0
- Volume máximo informado por el broker: 15.0
- Risk base value: 9479.00
- Risk target 1%: 94.79
- Actual risk amount registrado en metadata: 40.7085
- Margin del order_check: 868.65

Interpretación:

El volumen parece grande en comparación visual con otros símbolos, pero el riesgo
al Stop Loss que quedó registrado no supera el 1%; es inferior al objetivo.

La causa es que el volumen calculado necesario era mayor que el máximo permitido
por el broker. El daemon recortó al máximo de 15.0.

Por esta razón se implementó el rechazo de riesgo objetivo no alcanzable, además
del control independiente de margen.
