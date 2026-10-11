import pandas as pd
import pytest
from marketdata.zmq_provider import ZMQMarketDataProvider
from marketdata.factory import build_market_data_provider, ExternalMarketDataSettings


class MockFallbackProvider:
    def resolve_symbol(self, s):
        return s.upper()

    def ensure_symbol(self, s):
        return s.upper()

    def prepare_symbols(self, symbols):
        return [s.upper() for s in symbols]

    def get_symbol_info(self, s):
        return {"name": s, "point": 0.01, "digits": 2}

    def get_candles(self, symbol, timeframe="M5", count=10):
        return pd.DataFrame({
            "time": pd.date_range("2026-01-01", periods=count, freq="5min"),
            "open": [10.0] * count,
            "high": [12.0] * count,
            "low": [9.0] * count,
            "close": [11.0] * count,
            "tick_volume": [50] * count,
        })


def test_zmq_provider_fallback_when_offline():
    mock = MockFallbackProvider()
    provider = ZMQMarketDataProvider(fallback_provider=mock, timeout_ms=300)
    
    # Should not crash and should fall back gracefully
    assert provider.resolve_symbol("boom1000") == "BOOM1000"
    candles = provider.get_candles("boom1000", "M5", 5)
    assert len(candles) == 5
    assert "close" in candles.columns


def test_factory_builds_zmq_provider():
    mock = MockFallbackProvider()
    provider = build_market_data_provider(
        mock,
        settings=ExternalMarketDataSettings(mode="zmq")
    )
    assert isinstance(provider, ZMQMarketDataProvider)
