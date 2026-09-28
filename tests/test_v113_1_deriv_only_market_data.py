import json
import time

import pytest

from marketdata.cache import MarketDataCache
from marketdata.deriv import DerivMarketDataProvider
from marketdata.factory import ExternalMarketDataSettings, build_market_data_provider
from marketdata.normalization import MarketDataIdentity, MarketDataValidationError, normalize_candles
from marketdata.router import DerivOnlyMarketDataRouter
from marketdata.shadow import ShadowMarketDataProvider
from tools.market_data_shadow_report import summarize


class FakeTransport:
    def __init__(self):
        self.requests = []
        self.connected = 0

    def connect(self):
        self.connected += 1
        return True

    def disconnect(self):
        return True

    def request(self, payload):
        self.requests.append(dict(payload))
        if "active_symbols" in payload:
            return {"active_symbols": [
                {"display_name": "EUR/USD", "symbol": "frxEURUSD"},
                {"display_name": "Gold/USD", "symbol": "frxXAUUSD"},
                {"display_name": "Wall Street 30", "symbol": "OTC_DJI"},
                {"display_name": "Volatility 100 Index", "symbol": "R_100"},
            ]}
        if payload.get("style") == "ticks":
            return {"history": {"prices": [101.25], "times": [1_700_000_300]}}
        now = int(time.time())
        return {"candles": [
            {"epoch": now - 600, "open": 100, "high": 102, "low": 99, "close": 101},
            {"epoch": now - 300, "open": 101, "high": 103, "low": 100, "close": 102},
            {"epoch": now, "open": 102, "high": 104, "low": 101, "close": 103},
        ]}


class MetadataOnly:
    def __init__(self):
        self.connector = object()
        self.candle_reads = 0
        self.tick_reads = 0

    def connect(self): return True
    def disconnect(self): return True
    def resolve_symbol(self, symbol): return str(symbol)
    def ensure_symbol(self, symbol): return str(symbol)
    def search_symbols(self, text): return []
    def get_symbol_info(self, symbol): return {"name": str(symbol)}
    def get_candles(self, *args, **kwargs):
        self.candle_reads += 1
        raise AssertionError("MT5 candles forbidden outside shadow comparison")
    def get_current_tick(self, *args, **kwargs):
        self.tick_reads += 1
        raise AssertionError("MT5 tick forbidden outside shadow comparison/pre-fill")


def _provider(transport=None):
    return DerivMarketDataProvider(transport=transport or FakeTransport())


@pytest.mark.parametrize("execution,native", [
    ("EURUSD", "frxEURUSD"),
    ("XAUUSDmicro", "frxXAUUSD"),
    ("Wall Street 30", "OTC_DJI"),
    ("Volatility 100 Index", "R_100"),
])
def test_dynamic_mapping_covers_all_strategy_families(execution, native):
    assert _provider().resolve_native_symbol(execution) == native


def test_dynamic_mapping_supports_current_public_catalog_field_names():
    class CurrentPublicTransport(FakeTransport):
        def request(self, payload):
            self.requests.append(dict(payload))
            return {"active_symbols": [{
                "underlying_symbol_name": "Boom 900 Index",
                "underlying_symbol": "BOOM900",
                "market": "synthetic_index",
            }]}

    assert (
        _provider(CurrentPublicTransport()).resolve_native_symbol("Boom 900 Index")
        == "BOOM900"
    )


def test_unpublished_mt5_only_symbol_is_not_mapped_to_a_different_market():
    class CurrentPublicTransport(FakeTransport):
        def request(self, payload):
            self.requests.append(dict(payload))
            return {"active_symbols": [{
                "underlying_symbol_name": "Boom 900 Index",
                "underlying_symbol": "BOOM900",
            }]}

    with pytest.raises(MarketDataValidationError, match="no ofrece un equivalente"):
        _provider(CurrentPublicTransport()).resolve_native_symbol("Boom 99 Index")


def test_deriv_candles_are_canonical_and_preserve_open_candle():
    transport = FakeTransport()
    frame = _provider(transport).get_candles("EURUSD", "M5", 100)
    assert frame.attrs["market_data_source"] == "DERIV_CHARTS_WEBSOCKET"
    assert frame.attrs["native_symbol"] == "frxEURUSD"
    assert str(frame["time"].dt.tz) == "UTC"
    assert bool(frame.iloc[-1]["complete"]) is False


def test_active_symbols_uses_public_endpoint_contract_without_legacy_product_type():
    transport = FakeTransport()
    _provider(transport).active_symbols()
    request = next(row for row in transport.requests if "active_symbols" in row)
    assert request == {"active_symbols": "brief"}


def test_router_uses_deriv_for_forex_and_never_mt5_market_reads():
    transport, metadata = FakeTransport(), MetadataOnly()
    router = DerivOnlyMarketDataRouter(
        deriv_provider=_provider(transport), metadata_provider=metadata,
        cache=MarketDataCache(), candle_cache_ttl_seconds=60,
    )
    first = router.get_candles("EURUSD", "M5", 100)
    second = router.get_candles("EURUSD", "M5", 100)
    candle_requests = [row for row in transport.requests if row.get("style") == "candles"]
    assert len(candle_requests) == 1
    assert first.attrs["cache_hit"] is False
    assert second.attrs["cache_hit"] is True
    assert metadata.candle_reads == metadata.tick_reads == 0


def test_router_connects_deriv_lazily():
    transport = FakeTransport()
    router = DerivOnlyMarketDataRouter(
        deriv_provider=_provider(transport), metadata_provider=MetadataOnly(),
    )
    router.connect()
    assert transport.connected == 0


def test_factory_rejects_oanda_provider_name():
    settings = ExternalMarketDataSettings(mode="external", provider="oanda")
    with pytest.raises(Exception, match="sólo admite"):
        build_market_data_provider(MetadataOnly(), settings=settings)


def test_shadow_primary_survives_failed_mt5_comparison(tmp_path):
    class Primary:
        connector = object()
        def connect(self): return True
        def disconnect(self): return True
        def get_candles(self, symbol, timeframe, count):
            return normalize_candles([
                {"time": "2026-09-14T11:55:00Z", "open": 1, "high": 2, "low": .5, "close": 1.5},
                {"time": "2026-09-14T12:00:00Z", "open": 1.5, "high": 2, "low": 1, "close": 1.7},
            ], identity=MarketDataIdentity(symbol, "frxEURUSD", "DERIV"), timeframe=timeframe)

    class Reference:
        def get_candles(self, *args, **kwargs):
            raise RuntimeError("MT5 offline")

    output = tmp_path / "shadow.jsonl"
    result = ShadowMarketDataProvider(Primary(), Reference(), output_path=output).get_candles(
        "EURUSD", "M5", 10
    )
    row = json.loads(output.read_text(encoding="utf-8").strip())
    assert result.attrs["market_data_source"] == "DERIV"
    assert row["comparison_available"] is False
    assert "MT5 offline" in row["comparison_error"]


def test_shadow_report_missing_file_is_not_an_exception(tmp_path):
    assert summarize(tmp_path / "missing.jsonl") == []


def test_normalization_rejects_invalid_ohlc():
    with pytest.raises(MarketDataValidationError, match="OHLC inválido"):
        normalize_candles(
            [{"time": "2026-09-14T12:00:00Z", "open": 10, "high": 9, "low": 8, "close": 10}],
            identity=MarketDataIdentity("X", "Y", "DERIV"), timeframe="M5",
        )


def test_execute_worker_requires_both_demo_and_market_data_preflight():
    from pathlib import Path

    source = (Path(__file__).resolve().parents[1] / "app" / "main.py").read_text(
        encoding="utf-8"
    )
    worker = source[source.index("if args.mode in strategy_worker_modes:"):]
    worker = worker[:worker.index("live_modes =")]
    assert 'preflight = run_demo_preflight(symbols)' in worker
    assert 'market_preflight = run_market_data_preflight(args, symbols=symbols)' in worker
    assert 'if not market_preflight["ready"]' in worker
    assert 'symbols = market_preflight["symbols"]' in worker


def test_coordinator_does_not_restart_workers_rejected_by_preflight():
    from pathlib import Path

    source = (Path(__file__).resolve().parents[1] / "app" / "main.py").read_text(
        encoding="utf-8"
    )
    assert "if code == 2:" in source
    assert 'status="BLOCKED_PREFLIGHT"' in source
    assert 'blocked_profiles.add(profile)' in source
    assert "No se reiniciará automáticamente" in source
