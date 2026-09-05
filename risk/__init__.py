"""Paquete de gestión monetaria legado (`MoneyManager`).

Contiene `money_manager.MoneyManager`, una gestion de capital orientada a
objetos con seguimiento de balance, riesgo por operacion y drawdown.

ESTADO — LEGADO. No tiene consumidores en produccion: solo lo utiliza
`tests/test_money_manager.py`. La operativa real dimensiona el riesgo en
`strategy.execution.live_trading_engine`.

NO CONFUNDIR con `strategy/risk/`, que es otro paquete de riesgo distinto y
tambien fuera de la operativa real.
"""
