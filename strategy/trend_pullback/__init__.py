"""Paquete de la estrategia Trend Pullback H1 + M15 (BlackDaemonFX)."""
from strategy.trend_pullback.config import (
    DEFAULT_PULLBACK_SYMBOLS,
    TREND_PULLBACK_SCENARIO,
    TREND_PULLBACK_STRATEGY,
    TREND_PULLBACK_VERSION,
    TrendPullbackConfig,
)
from strategy.trend_pullback.trend_pullback_strategy import TrendPullbackStrategy, closed_candles_only

__all__ = [
    "DEFAULT_PULLBACK_SYMBOLS",
    "TREND_PULLBACK_SCENARIO",
    "TREND_PULLBACK_STRATEGY",
    "TREND_PULLBACK_VERSION",
    "TrendPullbackConfig",
    "TrendPullbackStrategy",
    "closed_candles_only",
]
