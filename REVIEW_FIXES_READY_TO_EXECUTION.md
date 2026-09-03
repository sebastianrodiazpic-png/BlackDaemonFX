# Correcciones aplicadas: READY_TO_ENTER -> EXECUTION

## 1. Error `KeyError: 'structure'`
Archivo: `strategy/execution/multi_timeframe.py`

La función `_get_h1_context()` ya no asume que el DataFrame H1 contiene la columna `structure`.

Orden de resolución:
1. Usa `get_current_trend()` cuando existe o se crea la columna `structure`.
2. Si no hay tendencia estructural HH/HL/LH/LL, infiere la dirección desde el último BOS/CHOCH alcista o bajista.
3. Si todavía no existe dirección, usa `result['summary']['trend']` cuando sea `BULLISH` o `BEARISH`.
4. Nunca llama a `get_current_trend()` con un DataFrame sin `structure`.

## 2. Error de sintaxis por indentación

La versión revisada del proyecto tenía el cuerpo de `_get_h1_context()` fuera de la función, produciendo `IndentationError`. Se reemplazó el bloque completo por una implementación correctamente indentada.

## 3. Contrato real de `trade_simulator.py`
Archivo: `tests/test_ready_to_execution_transition.py`

El simulador existente recibe:

```python
simulate_trade(df=..., trade=..., max_bars=...)
```

La prueba anterior intentaba llamar una API inexistente con `candles`, `direction`, `entry_time`, etc. La prueba ahora construye un `pd.Series` con:
- entry_time
- entry_price
- stop_loss
- take_profit
- trade_type (`long` para BUY y `short` para SELL)

También valida los estados reales del simulador:
- `win`
- `loss`
- `expired`
- `ambiguous`

Y usa `exit_reason`, que es el nombre real devuelto por `trade_simulator.py`.

## 4. Error lógico de frescura de la señal M5

La prueba mezclaba en la misma ventana:
- velas usadas para validar `READY_TO_ENTER`
- velas futuras destinadas a simular la ejecución

Eso envejecía artificialmente la señal M5 y producía `STALE_M5_SIGNAL`.

La prueba ahora configura `entry_candles=10` y el proveedor controlado devuelve la ventana inicial solicitada. Así:
- la señal de las 15:00 sigue fresca durante el análisis;
- las velas posteriores se recuperan después para la simulación.

## Resultado validado

Comando:

```powershell
python -m pytest -q tests/test_symbol_direction_policy.py tests/test_signal_freshness.py tests/test_multi_timeframe_sequence.py tests/test_ready_to_enter_transition.py tests/test_ready_to_execution_transition.py
```

Resultado:

```text
17 passed
```

La prueba principal `READY_TO_ENTER -> EXECUTION` termina en:

```text
MULTI_TIMEFRAME_SIGNAL: OK
STATE: READY_TO_ENTER
SIMULATION RESULT: win
EXIT PRICE: 115.0
REASON: take_profit
PRUEBA CONTROLADA EXITOSA
```
