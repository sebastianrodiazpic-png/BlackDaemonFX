"""Estrategia Opening Range Breakout (ORB) de la sesion de Nueva York.

Opera la rotura del rango formado en la apertura de Nueva York sobre indices y
oro (Wall Street 30, US Tech 100, S&P 500, XAUUSD).

Vinculaciones:
    - `strategy.orb.new_york_orb`: implementacion completa.
    - `app.main`: usa `discover_orb_symbols` para armar el universo del worker.
    - `strategy.execution.live_trading_engine`: ejecuta la estrategia.
"""

from .new_york_orb import (
    ORBConfig,
    NewYorkORBStrategy,
    is_orb_eligible_symbol,
    classify_orb_market,
    discover_orb_symbols,
)

__all__ = [
    "ORBConfig",
    "NewYorkORBStrategy",
    "is_orb_eligible_symbol",
    "classify_orb_market",
    "discover_orb_symbols",
]
