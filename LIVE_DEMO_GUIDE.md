# Live Demo SMC - Validación segura

El motor opera con la secuencia `H1 -> M15 -> M5`:

1. **H1:** contexto y tendencia.
2. **M15:** setup SMC alineado con H1.
3. **M5:** confirmación de entrada posterior al setup M15.
4. **Precio actual:** se adapta el Stop Loss estructural a las restricciones reales del símbolo.
5. **Riesgo:** se calcula el volumen usando `MetaTrader5.order_calc_profit` o el valor del tick.
6. **Validación:** `order_check` de MT5 comprueba la orden sin abrirla.
7. **Ejecución DEMO:** solo si `execution_enabled=True` y la cuenta conectada es DEMO.
8. **Persistencia:** se guarda señal, tickets de orden/deal/posición y riesgo real.
9. **Monitoreo:** las operaciones OPEN se sincronizan con el historial de MT5 y se actualiza PnL, comisión, swap, resultado y R:R realizado.

## Riesgo

Por defecto:

- `risk_percent = 1.0`
- `risk_base = EQUITY`
- `max_actual_risk_tolerance = 0.01`

El resultado muestra tanto `risk_amount` objetivo como `actual_risk_amount` calculado después de normalizar el volumen.

> Un valor de riesgo cercano a 99 no significa necesariamente 10%. El porcentaje debe comprobarse contra `risk_base_value`, que ahora se imprime explícitamente.

## Stops de Deriv / MT5

Antes de enviar una orden se consulta:

- `point`
- `digits`
- `trade_stops_level`
- `trade_freeze_level`
- `volume_min`, `volume_max`, `volume_step`
- `trade_tick_size`, `trade_tick_value`

Si el SL estructural ya fue cruzado por el mercado, la señal se rechaza. Si solo está demasiado cerca del precio para el instrumento, el SL se amplía hasta la distancia mínima y el TP se recalcula manteniendo el R:R.

## Prueba segura

Desde la raíz del proyecto:

```powershell
python -m tests.test_live_demo
```

El modo actual es DRY RUN validado: no abre órdenes, pero ejecuta `order_check`.

Resultados esperados:

- `DRY_RUN_VALIDATED`: señal válida y orden técnicamente aceptada por la comprobación.
- `REJECTED_INVALID_MARKET_STOP`: el precio actual ya invalidó el SL estructural o el stop no puede normalizarse.
- `REJECTED_ORDER_CHECK`: MT5 rechaza la orden antes de enviarla.
- `REJECTED_RISK_EXCEEDED`: el volumen normalizado supera el riesgo permitido.
- `NO_H1_CONTEXT`, `NO_M15_SETUP`, `NO_M5_CONFIRMATION`: la estrategia no está lista todavía.

## Antes de activar DEMO

1. Revisar `risk_base_value` y confirmar que `risk_amount` es aproximadamente el porcentaje configurado.
2. Revisar `actual_risk_amount`.
3. Confirmar `order_check=True`.
4. Revisar `stop_validation` y `symbol_constraints`.
5. Confirmar que la cuenta MT5 conectada es DEMO.
6. Ejecutar inicialmente con un solo símbolo y un límite de una posición.

Para abrir órdenes DEMO, cambiar explícitamente:

```python
LiveTradingConfig(
    execution_enabled=True,
    max_total_open_positions=1,
    max_open_positions_per_symbol=1,
    risk_percent=1.0,
    risk_base="EQUITY",
)
```

No activar ejecución real con este motor: `assert_demo_account()` bloquea cuentas que MT5 reporta como no-DEMO.

## Verificación de la corrección de confirmaciones M5

Después de esta corrección, un `CONFIRMED` compatible con la política ya no debe desaparecer al convertir `long/short` en `BUY/SELL`. En el siguiente LIVE DEMO es importante observar la diferencia entre:

```text
M5: confirmations > 0
```

y el resultado final. Si existe una confirmación posterior al setup M15 más reciente y dentro del límite de antigüedad, el flujo debe avanzar a:

```text
MULTI_TIMEFRAME_SIGNAL
```

Después de eso el motor live podrá continuar con la validación de mercado, SL/TP, volumen, riesgo y `order_check`.

