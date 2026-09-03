# DaemonBlackFx — Broker Truth Risk Engine y mejora de calidad de entrada

## Incidente detectado

En la prueba DEMO del 27-08-2026, `Step Index 400` abrió una posición BUY con volumen 3.58.
El bot registró un riesgo esperado cercano a USD 98.81, pero el resultado cerrado fue aproximadamente
USD -1002.40. Esto equivale a una discrepancia superior a 10x.

La causa técnica identificada fue que el cálculo de volumen priorizaba la fórmula:

`distancia / tick_size * tick_value`

antes de consultar a MT5. Para sintéticos de Deriv esa fórmula no debe considerarse fuente universal de
verdad monetaria.

## Cambio principal: MT5 como fuente de verdad

El sizing ahora usa siempre:

`mt5.order_calc_profit(order_type, symbol, volume, entry_price, stop_loss)`

Flujo:

1. Calcular pérdida de 1 lote con MT5.
2. Calcular volumen bruto para el riesgo objetivo.
3. Normalizar el volumen hacia abajo al `volume_step`.
4. Volver a calcular la pérdida con MT5 usando el volumen final.
5. Rechazar si el riesgo supera el límite.
6. Tras el fill, leer volumen, entrada y SL reales.
7. Recalcular riesgo real con MT5.
8. Si supera el hard cap, cerrar inmediatamente la posición y poner el símbolo en cuarentena.

## Hard cap

Configuración por defecto:

- riesgo objetivo: 1.00%
- tolerancia previa: 1%
- hard cap post-fill: 2%

Con un objetivo de USD 100, el hard cap es USD 102.

Una posición que aparezca con riesgo real superior activa:

`EMERGENCY_RISK_EXIT`

y el símbolo se guarda en:

`storage/risk_quarantine.json`

Un símbolo en cuarentena no vuelve a operarse automáticamente hasta revisión manual.

## Mejora de confirmaciones M5

Se endurece la calidad inicial de entrada:

- score mínimo: 85
- cuerpo mínimo de vela: 65%
- displacement: 1.35x rango medio
- rechazo del OB: obligatorio
- displacement: obligatorio
- micro estructura: obligatoria
- cierre fuerte: obligatorio
- máximo de toques al OB: 1
- entrada extendida: bloqueada por el límite existente de 0.50R

El cierre fuerte exige:

- BUY: cierre en el 30% superior del rango de la vela.
- SELL: cierre en el 30% inferior del rango de la vela.

## Nota sobre win rate

Estos cambios buscan mejorar la calidad de las entradas, pero no garantizan un 60%-70%.
El objetivo correcto es validar con una muestra suficiente y medir:

- win rate por score
- expectancy
- profit factor
- drawdown
- resultados por instrumento
- resultados LONG vs SHORT
- break even vs SL/TP

Se recomienda acumular al menos 100 operaciones cerradas después de aplicar la corrección de riesgo antes
de optimizar los umbrales de forma agresiva.
