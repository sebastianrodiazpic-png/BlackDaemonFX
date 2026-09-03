# Revisión integral aplicada

## Cambios principales

1. **Política central de dirección**
   - Boom: solo `BUY`.
   - Crash: solo `SELL`.
   - Otros sintéticos: sin restricción por defecto.
   - Se aplica en pipeline, análisis multi-timeframe y motor live como defensa final.

2. **Protección contra señales M5 antiguas**
   - Se añadió `max_m5_signal_age_candles=3`.
   - Una confirmación vieja ya no se reutiliza para abrir una operación a precio actual.
   - Esto evita casos como un BUY histórico cuyo SL estructural ya fue cruzado.

3. **Secuencia M15 -> M5 más estricta**
   - Se toma el setup M15 más reciente y solo una confirmación M5 posterior.
   - Las confirmaciones previas quedan descartadas.

4. **Diagnóstico de market stop enriquecido**
   - Señal original, precio de mercado, bid/ask, spread, movimiento señal->mercado, SL estructural y política de dirección.

5. **Sizing de riesgo más fiable**
   - `order_calc_profit` del broker se usa primero para estimar el riesgo por lote.
   - `tick_size/tick_value` queda como fallback.

6. **Live demo dirigido**
   - Prioriza 5 Boom + 5 Crash para validar explícitamente la política BUY/SELL.

7. **Tests nuevos**
   - `tests/test_symbol_direction_policy.py`.

## Validación realizada

- Compilación sintáctica de los módulos Python modificados: correcta.
- Tests de política de dirección: 3 passed.
- El entorno de revisión no tiene MetaTrader5 para Linux, por lo que los tests que importan directamente el paquete MT5 no se pudieron ejecutar aquí. Deben ejecutarse en el Windows/venv del bot.

## Configuración recomendada para la primera prueba

Mantener:

```python
LiveTradingConfig(
    execution_enabled=False,
    diagnostic_mode=True,
    validate_order_in_dry_run=True,
    max_m5_signal_age_candles=3,
    max_total_open_positions=3,
    max_open_positions_per_symbol=1,
)
```

No activar `execution_enabled=True` hasta revisar el resultado de varios ciclos DRY_RUN.

## Corrección posterior: confirmaciones M5 eliminadas por la política de dirección

### Causa raíz identificada

La función `_filter_by_policy()` se utilizaba en dos formatos distintos:

- `setup_type`: `long` / `short`
- `direction`: `BUY` / `SELL`

La implementación anterior siempre convertía la política `BUY` en `long` y `SELL` en `short`. Esto funcionaba para `setup_type`, pero después de convertir una confirmación a `direction=BUY/SELL`, el filtro comparaba por ejemplo `BUY == long`, eliminando todas las confirmaciones válidas.

Esto explica los diagnósticos donde el motor interno mostraba `CONFIRMED`, pero el resultado final terminaba en `NO_M5_CONFIRMATION` y `signal_found_in_m5=False`.

### Corrección aplicada

`_filter_by_policy()` ahora normaliza ambos lados mediante `normalize_direction()` antes de comparar. Por lo tanto acepta correctamente:

- `long` y `BUY` como `BUY`
- `short` y `SELL` como `SELL`

La política se mantiene estricta:

- Boom -> solo BUY
- Crash -> solo SELL

### Tests de regresión añadidos

Se añadieron pruebas para comprobar que:

1. `setup_type=long/short` sigue filtrándose correctamente.
2. `direction=BUY/SELL` no se elimina después de la conversión.
3. Una confirmación BUY válida de Boom permanece disponible para el análisis M5.

### Validación local

Ejecutado en el entorno de revisión:

```text
5 passed
```

Comando recomendado en Windows/venv del proyecto:

```powershell
python -m pytest tests/test_symbol_direction_policy.py tests/test_signal_freshness.py -q
python -m tests.test_live_demo
```


## Mejoras posteriores de investigación: secuencia y testabilidad

8. **Semántica real de la configuración M15 -> M5**
   - `require_latest_m15_setup=True`: exige que la confirmación M5 corresponda al setup M15 más reciente.
   - `require_latest_m15_setup=False`: permite retroceder al setup M15 anterior más reciente que sí tenga una confirmación M5 compatible.
   - `require_m5_after_m15=True`: exige el orden temporal M15 -> M5.
   - `require_m5_after_m15=False`: permite compatibilidad con secuencias sin ese requisito.
   - Antes de esta mejora ambas opciones existían en la configuración, pero el selector siempre se comportaba como si estuvieran activas.

9. **Diagnóstico auditable de la secuencia**
   - Se añadió `diagnostics.sequence` con:
     - total de setups M15;
     - total de confirmaciones M5;
     - configuración efectiva de las dos reglas temporales;
     - setup M15 seleccionado;
     - confirmación M5 seleccionada;
     - número de confirmaciones elegibles.
   - El live demo ahora imprime estos datos.

10. **Motor importable para pruebas sin MetaTrader5**
   - La importación de `MT5ExecutionProvider` pasó a ser diferida al momento de crear el motor.
   - Se eliminó la dependencia directa de `MetaTrader5` del módulo `live_trading_engine.py` cuando solo se prueban diagnósticos puros.
   - Esto permite ejecutar `test_signal_freshness.py` en entornos sin MT5 instalado.

11. **Pruebas nuevas**
   - Se añadió cobertura para el fallback temporal de señales cuyo timestamp no coincide exactamente con una vela M5.
   - Se añadió `tests/test_multi_timeframe_sequence.py` para las tres políticas de secuencia M15 -> M5.

### Validación de esta revisión

```text
15 passed
```

Suite amplia sin pruebas dependientes de MetaTrader5 en este entorno Linux:

```text
54 passed
```
