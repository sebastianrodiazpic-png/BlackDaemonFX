"""Fuentes de datos de mercado independientes del ejecutor MT5."""

from .factory import ExternalMarketDataSettings, build_market_data_provider
from .router import DerivOnlyMarketDataRouter, MarketDataConfigurationError

__all__ = [
    "DerivOnlyMarketDataRouter",
    "ExternalMarketDataSettings",
    "MarketDataConfigurationError",
    "build_market_data_provider",
]
