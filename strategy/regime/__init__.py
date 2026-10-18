"""Módulo de centinela y clasificación de regímenes de mercado.

Proporciona la Capa 1 (Macro / Escudo Protector) para identificar el entorno
estructural del mercado (tendencia limpia, rango operable o ruido tóxico)
antes de ejecutar operaciones.
"""
from strategy.regime.market_regime_sentinel import (
    MarketRegimeClassification,
    MarketRegimeConfig,
    MarketRegimeDecision,
    MarketRegimeMetrics,
    MarketRegimeSentinel,
    REGIME_CLEAN_RANGE,
    REGIME_HIGH_VOLATILITY,
    REGIME_STABLE_TREND,
    REGIME_TOXIC_NOISE,
    classify_market_regime,
    compute_regime_metrics,
)

__all__ = [
    "MarketRegimeClassification",
    "MarketRegimeConfig",
    "MarketRegimeDecision",
    "MarketRegimeMetrics",
    "MarketRegimeSentinel",
    "REGIME_CLEAN_RANGE",
    "REGIME_HIGH_VOLATILITY",
    "REGIME_STABLE_TREND",
    "REGIME_TOXIC_NOISE",
    "classify_market_regime",
    "compute_regime_metrics",
]
