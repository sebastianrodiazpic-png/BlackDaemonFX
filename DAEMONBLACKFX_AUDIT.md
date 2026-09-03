# DaemonBlackFx — Auditoría técnica y mejoras de gestión de riesgo

## Objetivo de esta revisión
Esta revisión analiza dos controles críticos del daemon conectado a Deriv mediante MetaTrader 5:

1. **Break Even automático**: mover el Stop Loss al precio real de apertura cuando la posición alcanza el múltiplo R configurado.
2. **Riesgo por operación**: impedir que se ejecute una orden cuyo riesgo monetario real quede materialmente por debajo o por encima del objetivo configurado.

La política propuesta no “fuerza” una operación al 1% cuando el broker no permite el volumen necesario. En ese caso la operación debe ser **rechazada**, porque abrirla con 0.43% cambia la estrategia y distorsiona las estadísticas.

---

## Hallazgo 1 — Break Even ya existía, pero tenía ventanas operativas

El motor contiene `_monitor_break_even_positions()` y la lógica calcula correctamente:

- BUY: `trigger = entry + (entry - initial_sl) * trigger_rr`
- SELL: `trigger = entry - (initial_sl - entry) * trigger_rr`

Al cumplirse el trigger, llama a `MT5TradeExecutor.move_stop_loss()`, que a su vez usa `TRADE_ACTION_SLTP`.

### Problemas operativos detectados

- El daemon imponía un intervalo mínimo de 30 segundos.
- Una posición sintética puede alcanzar 1R y retroceder dentro de esa ventana.
- El modo `run_once()` no ejecutaba el monitor de Break Even.
- El monitor solo se ejecutaba una vez por ciclo.

### Corrección aplicada

- Se permite una frecuencia mínima de 1 segundo.
- `run_once()` revisa Break Even antes y después del procesamiento.
- El daemon continúa revisando las posiciones en cada ciclo.
- La operación se marca como `break_even_activated` para evitar modificaciones repetidas.

### Recomendación operativa

Para pruebas DEMO con sintéticos rápidos:

```bash
py -m app.main --mode demo-daemon --execute --interval 5 --risk-percent 1.0 --min-rr 2.0
```

Para instrumentos extremadamente rápidos, usar 1–3 segundos si el consumo de CPU y las consultas a MT5 lo permiten.

---

## Hallazgo 2 — Volatility 75 Index se abrió con 0.43% de riesgo

En el reporte de prueba:

| Instrumento | Riesgo objetivo | Riesgo real | Riesgo real % | Volumen |
|---|---:|---:|---:|---:|
| Volatility 75 Index | 94.79 | 40.71 | 0.429% | 15.00 |

El diagnóstico indica que el volumen máximo del símbolo era **15.0**, mientras que el volumen necesario para alcanzar el riesgo objetivo era superior.

Esto significa que el 1% era **inalcanzable con la configuración del símbolo y ese Stop Loss**. La decisión correcta es rechazar la operación, no abrirla con un riesgo distinto.

## Política de riesgo aplicada

- Riesgo objetivo: `risk_base * risk_percent / 100`
- Base por defecto: `EQUITY`
- Riesgo máximo permitido: objetivo + tolerancia configurada.
- Riesgo mínimo aceptable: `99%` del objetivo por defecto.
- Si el broker limita el volumen y el riesgo alcanzable queda bajo ese umbral:
  - `REJECTED_RISK_TARGET_UNREACHABLE`
  - `BROKER_VOLUME_LIMIT_PREVENTS_TARGET_RISK`

El resultado de sizing ahora deja explícitos:

- `actual_risk_amount`
- `actual_risk_ratio`
- `actual_risk_percent`
- `min_required_risk`
- `min_actual_risk_ratio`
- `raw_volume`
- `volume_max`

### Nota sobre “exactamente 1%”

No siempre es matemáticamente posible ejecutar exactamente 1.0000% debido a:

- `volume_step`
- `volume_min`
- `volume_max`
- distancia del SL
- valor del tick

Por eso el sistema debe usar una banda de aceptación y rechazar operaciones estructuralmente inalcanzables. Si se requiere máxima estrictitud, se puede subir `min_actual_risk_ratio` a `0.999` o `1.0`, sabiendo que aumentará la cantidad de señales rechazadas.

---

## Lectura del reporte de prueba

Los trades con metadata moderna muestran que el sizing funciona razonablemente bien en la mayoría de los símbolos:

- High Frequency Vol 100: ~0.981%
- Volatility 30 (1s): ~1.000%
- Volatility 100: ~1.000%
- Volatility 50 (1s): ~0.997%
- Step Index: ~0.995%
- Volatility 25: ~1.000%
- Boom 500: ~1.000%
- Volatility 75: **~0.429% — debe rechazarse**

Las operaciones antiguas de Boom 100 no contienen la metadata moderna de riesgo, por lo que deben tratarse como registros de una versión anterior del pipeline.

---

## Arquitectura de ejecución recomendada

```text
H1 Context
   ↓
M15 Setup
   ↓
M5 Confirmation
   ↓
Signal Freshness
   ↓
Current Market Price
   ↓
Validate Structural SL / Broker Stops
   ↓
Calculate Broker-Aware Volume
   ↓
Risk Target Policy
   ├─ reachable → Order Check → Execute
   └─ unreachable → Reject and log
   ↓
Position Monitoring Loop
   ├─ initial risk
   ├─ 1R reached?
   ├─ move SL to real entry
   ├─ verify broker response
   └─ persist BE state
   ↓
Closed Trade Synchronization
   ↓
Reporting
```

---

## Próximos puntos de mejora recomendados

### Prioridad alta

1. Verificar el SL real después de `TRADE_ACTION_SLTP`, leyendo nuevamente la posición desde MT5.
2. Registrar cada evento de Break Even en una tabla/event log independiente.
3. Añadir `break_even_offset_points` para cubrir spread/comisión si se desea BE+.
4. Separar claramente riesgo planificado, riesgo ejecutado y riesgo realizado.
5. Bloquear nuevas entradas si la suma del riesgo abierto supera un presupuesto global.

### Prioridad media

1. Trailing Stop por R después del Break Even.
2. Gestión parcial: cerrar 50% en 1R y mover el resto a BE.
3. Dashboard por instrumento con win rate, expectancy, PF y drawdown.
4. Alertas cuando un símbolo rechaza repetidamente operaciones por `volume_max`.
5. Versionar la configuración completa dentro de cada trade.

### Calidad de código

- Mantener `LiveTradingEngine` como orquestador.
- Mantener la lógica MT5 dentro de `brokers/`.
- Mantener cálculos financieros puros dentro de `risk/`.
- Toda transición de posición debe tener una prueba automatizada.
- Evitar duplicar la lógica de sizing entre backtest y live execution.

---

## Pruebas mínimas antes de volver a DEMO

- [ ] BUY alcanza 1R → SL se mueve a entrada.
- [ ] SELL alcanza 1R → SL se mueve a entrada.
- [ ] Reiniciar daemon después de abrir trade → BE sigue funcionando.
- [ ] BE ya activo → no enviar otra modificación.
- [ ] MT5 rechaza modificación → no marcar BE como activado.
- [ ] Volumen máximo impide 1% → trade rechazado.
- [ ] Volumen mínimo supera 1% + tolerancia → trade rechazado.
- [ ] Step de volumen deja riesgo dentro de banda → trade permitido.
- [ ] Riesgo abierto total no excede presupuesto.
- [ ] Reporte muestra riesgo objetivo y riesgo real por trade.

