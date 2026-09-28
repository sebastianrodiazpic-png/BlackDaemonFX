import json
import time

import pytest

from marketdata.cache import MarketDataCache
from marketdata.deriv import DerivMarketDataProvider
from marketdata.normalization import MarketDataIdentity, MarketDataValidationError, normalize_candles
from marketdata.oanda import OandaMarketDataProvider
from marketdata.router import ExternalMarketDataRouter, MarketDataConfigurationError
from marketdata.shadow import ShadowMarketDataProvider


class FakeDerivTransport:
    def __init__(self): self.requests = []
    def connect(self): return True
    def disconnect(self): return True
    def request(self, payload):
        self.requests.append(dict(payload))
        if payload.get("style") == "ticks":
            return {"history": {"prices": [101.25], "times": [1_700_000_300]}}
        now = int(time.time())
        return {"candles": [
            {"epoch": now - 600, "open": 100, "high": 102, "low": 99, "close": 101},
            {"epoch": now - 300, "open": 101, "high": 103, "low": 100, "close": 102},
            {"epoch": now, "open": 102, "high": 104, "low": 101, "close": 103},
        ]}


class FakeOandaTransport:
    def get(self, path, params=None):
        if "/pricing" in path:
            return {"prices": [{
                "time": "2026-09-11T12:00:01Z",
                "bids": [{"price": "1.1000", "liquidity": 10}],
                "asks": [{"price": "1.1002", "liquidity": 12}],
            }]}
        return {"candles": [
            {"time": "2026-09-11T11:50:00Z", "volume": 80, "complete": True,
             "mid": {"o": "1.1", "h": "1.2", "l": "1.0", "c": "1.15"}},
            {"time": "2026-09-11T11:55:00Z", "volume": 90, "complete": False,
             "mid": {"o": "1.15", "h": "1.25", "l": "1.1", "c": "1.2"}},
        ]}


class MetadataOnlyProvider:
    def __init__(self): self.connector, self.candle_reads, self.tick_reads = object(), 0, 0
    def connect(self): return True
    def disconnect(self): return True
    def resolve_symbol(self, symbol): return str(symbol)
    def ensure_symbol(self, symbol): return str(symbol)
    def get_symbol_info(self, symbol): return {"name": str(symbol), "point": .01, "digits": 2}
    def search_symbols(self, text): return []
    def get_candles(self, *a, **k): self.candle_reads += 1; raise AssertionError("MT5 candles forbidden")
    def get_current_tick(self, *a, **k): self.tick_reads += 1; raise AssertionError("MT5 ticks forbidden")


class ConnectCountingProvider:
    source_name = "COUNTING"
    def __init__(self): self.connections = 0
    def connect(self): self.connections += 1; return True
    def disconnect(self): return True


def test_normalization_rejects_invalid_ohlc():
    with pytest.raises(MarketDataValidationError, match="OHLC invalido"):
        normalize_candles(
            [{"time": "2026-09-11T12:00:00Z", "open": 10, "high": 9, "low": 8, "close": 10}],
            identity=MarketDataIdentity("X", "Y", "TEST"), timeframe="M5",
        )


def test_deriv_provider_returns_canonical_data():
    transport = FakeDerivTransport()
    provider = DerivMarketDataProvider(symbol_map={"Volatility 100 Index": "R_100"}, transport=transport)
    candles = provider.get_candles("Volatility 100 Index", "M5", 100)
    assert str(candles["time"].dt.tz) == "UTC"
    assert candles.attrs["market_data_source"] == "DERIV_WEBSOCKET"
    assert bool(candles.iloc[-1]["complete"]) is False
    assert provider.get_current_tick("Volatility 100 Index")["last"] == pytest.approx(101.25)


def test_oanda_maps_forex_and_volume():
    provider = OandaMarketDataProvider(token="test", account_id="account", transport=FakeOandaTransport())
    candles = provider.get_candles("EURUSD", "M5", 20)
    assert candles.attrs["native_symbol"] == "EUR_USD"
    assert candles["tick_volume"].tolist() == [80.0, 90.0]
    assert candles.attrs["volume_reliable"] is True
    tick = provider.get_current_tick("EURUSD")
    assert tick["bid"] == pytest.approx(1.1000) and tick["ask"] == pytest.approx(1.1002)


def test_router_never_uses_mt5_market_data_and_caches():
    transport, metadata = FakeDerivTransport(), MetadataOnlyProvider()
    router = ExternalMarketDataRouter(
        deriv_provider=DerivMarketDataProvider(
            symbol_map={"Volatility 100 Index": "R_100"}, transport=transport,
        ), oanda_provider=None, metadata_provider=metadata,
        cache=MarketDataCache(), candle_cache_ttl_seconds=60,
    )
    first = router.get_candles("Volatility 100 Index", "M5", 100)
    second = router.get_candles("Volatility 100 Index", "M5", 100)
    assert len(transport.requests) == 1
    assert first.attrs["cache_hit"] is False and second.attrs["cache_hit"] is True
    assert metadata.candle_reads == metadata.tick_reads == 0


def test_router_does_not_eagerly_connect_unused_external_sources():
    deriv, oanda, metadata = ConnectCountingProvider(), ConnectCountingProvider(), MetadataOnlyProvider()
    router = ExternalMarketDataRouter(
        deriv_provider=deriv, oanda_provider=oanda, metadata_provider=metadata,
    )
    assert router.connect() is True
    assert deriv.connections == 0
    assert oanda.connections == 0


def test_router_fails_closed_without_oanda():
    router = ExternalMarketDataRouter(deriv_provider=object(), oanda_provider=None)
    with pytest.raises(MarketDataConfigurationError, match="OANDA no configurado"):
        router.get_candles("EURUSD", "M5", 10)


def test_shadow_keeps_external_when_reference_fails(tmp_path):
    class Primary:
        connector = object()
        def connect(self): return True
        def disconnect(self): return True
        def get_candles(self, symbol, timeframe, count):
            return normalize_candles([
                {"time": "2026-09-11T11:55:00Z", "open": 1, "high": 2, "low": .5, "close": 1.5},
                {"time": "2026-09-11T12:00:00Z", "open": 1.5, "high": 2, "low": 1, "close": 1.7},
            ], identity=MarketDataIdentity(symbol, "EUR_USD", "EXTERNAL"), timeframe=timeframe)
    class Reference:
        def get_candles(self, *a, **k): raise RuntimeError("MT5 offline")
    output = tmp_path / "shadow.jsonl"
    result = ShadowMarketDataProvider(Primary(), Reference(), output_path=output).get_candles("EURUSD", "M5", 10)
    record = json.loads(output.read_text(encoding="utf-8").strip())
    assert result.attrs["market_data_source"] == "EXTERNAL"
    assert record["comparison_available"] is False and "MT5 offline" in record["comparison_error"]
