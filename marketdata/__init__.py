"""Fuentes de datos de mercado independientes del ejecutor MT5."""

from .factory import ExternalMarketDataSettings, build_market_data_provider
from .router import DerivOnlyMarketDataRouter, ExternalMarketDataRouter, MarketDataConfigurationError

__all__ = [
    "DerivOnlyMarketDataRouter",
    "ExternalMarketDataRouter",
    "ExternalMarketDataSettings",
    "MarketDataConfigurationError",
    "build_market_data_provider",
]
