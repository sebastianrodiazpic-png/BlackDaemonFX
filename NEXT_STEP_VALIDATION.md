# Validación positiva end-to-end en DRY RUN

## Objetivo

Esta versión añade una prueba positiva controlada que demuestra que el motor puede recorrer la ruta completa:

H1/M15/M5 válido -> señal fresca -> precio actual válido -> SL/TP -> sizing -> riesgo -> MT5 order_check -> DRY_RUN_VALIDATED

sin llamar a `place_market_order`.

## Cambio de testabilidad

`LiveTradingEngine` acepta ahora un parámetro opcional `executor`.

- Producción: si no se entrega `executor`, crea `MT5ExecutionProvider(provider.connector)` como antes.
- Pruebas: se puede inyectar un executor falso para validar la lógica sin MetaTrader5 ni una cuenta conectada.

## Nueva prueba

`tests/test_live_end_to_end_dry_run.py`

La prueba controla:

1. Señal MTF válida.
2. Dirección BUY permitida para un símbolo sin restricción.
3. Señal M5 fresca y secuencia válida en los diagnósticos.
4. Cuenta DEMO.
5. Precio actual dentro del máximo drift permitido.
6. SL/TP válidos.
7. Cálculo de volumen.
8. Riesgo real no superior al límite.
9. `order_check` válido.
10. Resultado final `DRY_RUN_VALIDATED`.
11. Ausencia de llamada a `place_market_order`.

## Comando recomendado

```bash
python -m pytest tests/test_symbol_direction_policy.py tests/test_signal_freshness.py tests/test_multi_timeframe_sequence.py tests/test_live_end_to_end_dry_run.py -q
```

Resultado esperado en esta versión:

```text
16 passed
```

## Nota sobre el suite completo

En un entorno sin el paquete `MetaTrader5`, el suite completo puede fallar durante la colección de pruebas que importan directamente MetaTrader5. Esto no invalida las 16 pruebas puras anteriores; para ejecutar todo el suite se requiere el entorno MT5 instalado y configurado.
