# DaemonBlackFx – Cambios completos 2026-08-26

## Objetivo
Corregir y endurecer tres áreas:

1. Diagnóstico de `STATUS: NOT READY` en el preflight DEMO.
2. Break Even real y confirmado por MT5.
3. Separación entre frecuencia de análisis SMC y frecuencia de monitoreo de posiciones.

---

## 1. Preflight DEMO sin ambigüedad

Archivo: `services/execution_preflight_service.py` + `app/main.py`

El preflight sigue validando:

- información de cuenta MT5;
- conexión del terminal;
- AutoTrading / Trade API;
- cuenta DEMO;
- margen libre;
- base de datos SQLite;
- cada símbolo solicitado;
- restricciones mínimas del símbolo.

Ahora, cuando el resultado no está listo, la salida incluye una sección explícita:

```text
STATUS: NOT READY
FAILED CHECKS:
 - MT5_AUTOTRADING_ALLOWED: AUTO_TRADING_DISABLED_OR_TRADE_API_DISABLED | details=...
```

No se modifica ni se omite ninguna protección. Si el terminal no permite trading automático, la ejecución sigue bloqueada.

---

## 2. Break Even confirmado por el broker

Archivo: `strategy/execution/live_trading_engine.py`

Flujo actual:

1. Lee operaciones `OPEN` del bot desde SQLite.
2. Obtiene la posición real desde MT5 mediante el ticket de posición.
3. Recupera el `initial_stop_loss` persistido al abrir la operación.
4. Calcula el precio 1R usando el riesgo inicial.
5. BUY: activa cuando `current_price >= entry + initial_risk * RR`.
6. SELL: activa cuando `current_price <= entry - initial_risk * RR`.
7. Solicita la modificación real del SL a MT5.
8. Vuelve a consultar la posición real hasta 3 veces por defecto.
9. Solo persiste `break_even_activated=True` si MT5 confirma que el SL está realmente en el precio de entrada.
10. Si MT5 acepta la solicitud pero el SL no se refleja, registra `BREAK_EVEN_NOT_CONFIRMED_BY_BROKER` y no marca la operación como protegida.

Configuración añadida:

```python
break_even_confirmation_retries = 3
break_even_confirmation_delay_seconds = 0.20
```

---

## 3. Dos relojes independientes en el daemon

Antes, el mismo intervalo controlaba:

- análisis SMC;
- nuevas entradas;
- Break Even.

Ahora:

- `--interval`: frecuencia del análisis SMC y búsqueda de nuevas señales.
- `--position-monitor-interval`: frecuencia de monitoreo de posiciones, Break Even y sincronización.

Valores recomendados:

```text
--interval 30
--position-monitor-interval 2
```

Esto permite analizar H1/M15/M5 cada 30 segundos sin esperar 30 segundos para proteger una posición que alcance 1R.

---

## 4. Comandos

### Diagnóstico de un único instrumento

```cmd
py -m app.main --mode demo-preflight --symbol "Volatility 75 Index"
```

### Diagnóstico de todos los instrumentos configurados

```cmd
py -m app.main --mode demo-preflight
```

### Daemon DEMO solo análisis

```cmd
py -m app.main --mode demo-daemon --interval 30 --position-monitor-interval 2 --risk-percent 1.0 --min-rr 1.5
```

### Daemon DEMO con ejecución real en la cuenta DEMO

```cmd
py -m app.main --mode demo-daemon --execute --interval 30 --position-monitor-interval 2 --risk-percent 1.0 --min-rr 1.5
```

### Smoke test DEMO

Solo después de que el preflight indique `READY FOR DEMO EXECUTION`:

```cmd
py -m app.main --mode live-demo-smoke --confirm-live-demo --symbol "Volatility 75 Index"
```

---

## 5. Riesgo por operación

La política existente se mantiene y se documenta como obligatoria:

- riesgo objetivo = equity o balance × `risk_percent`;
- por defecto, la base es `EQUITY`;
- no se permite exceder el objetivo más allá de la tolerancia configurada;
- el riesgo real debe alcanzar al menos el 99% del riesgo objetivo;
- si el `volume_max` del broker impide alcanzar ese riesgo mínimo, la operación se rechaza;
- no se abre una operación silenciosamente con 0.43% cuando la estrategia exige aproximadamente 1%.

Resultado esperado:

```text
REJECTED_RISK_TARGET_UNREACHABLE
BROKER_VOLUME_LIMIT_PREVENTS_TARGET_RISK
```

---

## 6. Pruebas ejecutadas

Se ejecutaron pruebas para:

- preflight con información de símbolo tipo objeto;
- preflight con información de símbolo tipo diccionario;
- activación de Break Even en 1R;
- idempotencia de Break Even;
- rechazo de Break Even cuando MT5 no confirma el SL;
- política de riesgo objetivo no alcanzable;
- integración del daemon.

Resultado del conjunto ejecutado:

```text
9 passed
```
