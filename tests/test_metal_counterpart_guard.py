from types import SimpleNamespace
import pandas as pd
import pytest

from strategy.execution.live_trading_engine import LiveTradingEngine, LiveTradingConfig
from strategy.orb.new_york_orb import (
    classify_orb_market,
    is_orb_gold_symbol,
    is_orb_silver_symbol,
)


class DummyRepository:
    def __init__(self, trades=None):
        self.trades = list(trades or [])

    def open_trades(self, source=None):
        return [t for t in self.trades if t.get("status", "OPEN") == "OPEN"]

    def save_trade(self, trade):
        self.trades.append(trade)
        return len(self.trades)

    def get_trade_by_execution_key(self, key):
        for t in self.trades:
            if t.get("execution_key") == key:
                return t
        return None


class DummyDataProvider:
    def __init__(self, tick_size=0.01):
        self._tick_size = tick_size
        self.connector = SimpleNamespace()

    def resolve_symbol(self, s):
        return str(s)

    def ensure_symbol(self, s):
        return str(s)

    def get_tick_size(self, s):
        return self._tick_size

    def get_current_tick(self, s):
        return {"bid": 2500.0, "ask": 2500.1, "time": "2026-09-29T14:00:00Z"}

    def get_candles(self, symbol, timeframe, count=30):
        return pd.DataFrame({
            "time": pd.date_range("2026-09-29 10:00", periods=count, freq="5min", tz="UTC"),
            "open": [2500.0] * count,
            "high": [2505.0] * count,
            "low": [2495.0] * count,
            "close": [2502.0] * count,
            "tick_volume": [100] * count,
        })


def _make_engine(profile: str = "GOLD", repo: DummyRepository = None) -> LiveTradingEngine:
    engine = object.__new__(LiveTradingEngine)
    engine.config = LiveTradingConfig(
        bot_profile=profile,
        source="DEMO",
        magic=26082026,
        execution_enabled=True,
        gold_smc_session_enabled=False,  # disabled session restriction for isolated logic tests
    )
    engine.repository = repo or DummyRepository()
    engine.provider = DummyDataProvider()
    engine.executor = SimpleNamespace(
        normalize_market_stops=lambda s, e, sl, tp, d: (sl, tp),
        get_position=lambda t: None,
    )
    engine.lifecycle_manager = SimpleNamespace()
    engine._orb_gold_cycle_selection = None
    engine._orb_gold_cycle_diagnostics = None
    return engine


def test_metal_classification_standard_and_micro():
    # Gold variants
    assert classify_orb_market("XAUUSD") == "XAUUSD"
    assert classify_orb_market("XAUUSDmicro") == "MICRO_XAUUSD"
    assert classify_orb_market("microXAUUSD") == "MICRO_XAUUSD"
    assert classify_orb_market("XXAUUSD") == "XAUUSD"
    assert classify_orb_market("XXAUUSDmicro") == "MICRO_XAUUSD"
    assert is_orb_gold_symbol("XAUUSD") is True
    assert is_orb_gold_symbol("XAUUSDmicro") is True

    # Silver variants (including XXAGUSDmicro explicitly requested)
    assert classify_orb_market("XAGUSD") == "XAGUSD"
    assert classify_orb_market("XAGUSDmicro") == "MICRO_XAGUSD"
    assert classify_orb_market("XXAGUSDmicro") == "MICRO_XAGUSD"
    assert classify_orb_market("XXAGUSD") == "XAGUSD"
    assert is_orb_silver_symbol("XAGUSD") is True
    assert is_orb_silver_symbol("XXAGUSDmicro") is True
    assert is_orb_silver_symbol("XAGUSDmicro") is True


def test_gold_worker_blocks_xauusd_when_xauusdmicro_is_open():
    repo = DummyRepository(trades=[
        {
            "id": 1,
            "instrument": "XAUUSDmicro",
            "direction": "BUY",
            "status": "OPEN",
            "broker_position_ticket": "1001",
        }
    ])
    engine = _make_engine("GOLD", repo=repo)

    counterpart = engine._metal_counterpart_open("XAUUSD")
    assert counterpart is not None
    assert counterpart["metal"] == "GOLD"
    assert counterpart["instrument"] == "XAUUSDmicro"
    assert counterpart["action"] == "GOLD_COUNTERPART_EXPOSURE_ALREADY_OPEN"
    assert counterpart["reason"] == "YA_EXISTE_POSICION_ABIERTA_EN_CONTRATO_CONTRAPARTE_DE_ORO"

    # Also test through position limit result
    limit_res = engine._position_limit_result("XAUUSD", "exec_key_1")
    assert limit_res is not None
    assert limit_res["action"] == "GOLD_COUNTERPART_EXPOSURE_ALREADY_OPEN"


def test_gold_worker_blocks_xauusdmicro_when_xauusd_is_open():
    repo = DummyRepository(trades=[
        {
            "id": 2,
            "instrument": "XAUUSD",
            "direction": "SELL",
            "status": "OPEN",
            "broker_position_ticket": "1002",
        }
    ])
    engine = _make_engine("GOLD", repo=repo)

    counterpart = engine._metal_counterpart_open("XAUUSDmicro")
    assert counterpart is not None
    assert counterpart["metal"] == "GOLD"
    assert counterpart["instrument"] == "XAUUSD"
    assert counterpart["action"] == "GOLD_COUNTERPART_EXPOSURE_ALREADY_OPEN"

    limit_res = engine._position_limit_result("XAUUSDmicro", "exec_key_2")
    assert limit_res is not None
    assert limit_res["action"] == "GOLD_COUNTERPART_EXPOSURE_ALREADY_OPEN"


def test_silver_blocks_xagusd_when_xxagusdmicro_is_open():
    repo = DummyRepository(trades=[
        {
            "id": 3,
            "instrument": "XXAGUSDmicro",
            "direction": "BUY",
            "status": "OPEN",
            "broker_position_ticket": "1003",
        }
    ])
    engine = _make_engine("GOLD", repo=repo)

    counterpart = engine._metal_counterpart_open("XAGUSD")
    assert counterpart is not None
    assert counterpart["metal"] == "SILVER"
    assert counterpart["instrument"] == "XXAGUSDmicro"
    assert counterpart["action"] == "SILVER_COUNTERPART_EXPOSURE_ALREADY_OPEN"
    assert counterpart["reason"] == "YA_EXISTE_POSICION_ABIERTA_EN_CONTRATO_CONTRAPARTE_DE_PLATA"

    limit_res = engine._position_limit_result("XAGUSD", "exec_key_3")
    assert limit_res is not None
    assert limit_res["action"] == "SILVER_COUNTERPART_EXPOSURE_ALREADY_OPEN"


def test_silver_blocks_xxagusdmicro_when_xagusd_is_open():
    repo = DummyRepository(trades=[
        {
            "id": 4,
            "instrument": "XAGUSD",
            "direction": "SELL",
            "status": "OPEN",
            "broker_position_ticket": "1004",
        }
    ])
    engine = _make_engine("GOLD", repo=repo)

    counterpart = engine._metal_counterpart_open("XXAGUSDmicro")
    assert counterpart is not None
    assert counterpart["metal"] == "SILVER"
    assert counterpart["instrument"] == "XAGUSD"
    assert counterpart["action"] == "SILVER_COUNTERPART_EXPOSURE_ALREADY_OPEN"

    limit_res = engine._position_limit_result("XXAGUSDmicro", "exec_key_4")
    assert limit_res is not None
    assert limit_res["action"] == "SILVER_COUNTERPART_EXPOSURE_ALREADY_OPEN"


def test_silver_blocks_xagusdmicro_when_xagusd_is_open():
    repo = DummyRepository(trades=[
        {
            "id": 5,
            "instrument": "XAGUSD",
            "direction": "BUY",
            "status": "OPEN",
            "broker_position_ticket": "1005",
        }
    ])
    engine = _make_engine("GOLD", repo=repo)

    counterpart = engine._metal_counterpart_open("XAGUSDmicro")
    assert counterpart is not None
    assert counterpart["metal"] == "SILVER"
    assert counterpart["instrument"] == "XAGUSD"
    assert counterpart["action"] == "SILVER_COUNTERPART_EXPOSURE_ALREADY_OPEN"


def test_gold_open_does_not_block_silver():
    repo = DummyRepository(trades=[
        {
            "id": 6,
            "instrument": "XAUUSD",
            "direction": "BUY",
            "status": "OPEN",
            "broker_position_ticket": "1006",
        }
    ])
    engine = _make_engine("GOLD", repo=repo)

    assert engine._metal_counterpart_open("XAGUSD") is None
    assert engine._metal_counterpart_open("XXAGUSDmicro") is None


def test_silver_open_does_not_block_gold():
    repo = DummyRepository(trades=[
        {
            "id": 7,
            "instrument": "XAGUSD",
            "direction": "BUY",
            "status": "OPEN",
            "broker_position_ticket": "1007",
        }
    ])
    engine = _make_engine("GOLD", repo=repo)

    assert engine._metal_counterpart_open("XAUUSD") is None
    assert engine._metal_counterpart_open("XAUUSDmicro") is None


def test_closed_trades_do_not_block_counterpart():
    repo = DummyRepository(trades=[
        {
            "id": 8,
            "instrument": "XAUUSDmicro",
            "direction": "BUY",
            "status": "CLOSED",
            "broker_position_ticket": "1008",
        }
    ])
    engine = _make_engine("GOLD", repo=repo)

    assert engine._metal_counterpart_open("XAUUSD") is None


def test_diagnostics_track_counterpart_trades():
    repo = DummyRepository(trades=[
        {
            "id": 9,
            "instrument": "XAUUSDmicro",
            "direction": "BUY",
            "status": "OPEN",
            "broker_position_ticket": "1009",
        }
    ])
    engine = _make_engine("GOLD", repo=repo)

    diag = engine._open_trade_diagnostics("XAUUSD")
    assert diag["symbol_open"] == 0
    assert diag["counterpart_open"] == 1
    assert len(diag["counterpart_open_trades"]) == 1
    assert diag["counterpart_open_trades"][0]["instrument"] == "XAUUSDmicro"
