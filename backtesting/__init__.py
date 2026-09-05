"""Paquete de backtesting VIVO: evaluación histórica de estrategias.

Flujo: `backtest_pipeline` orquesta `trade_simulator` ->
`backtest_money_management` -> `backtest_storage`.

Lo invoca `app.main` desde la interfaz. Es el motor de backtest real del
proyecto; `strategy/backtest/` solo contiene un calculador de metricas sin
consumidores en produccion.
"""
