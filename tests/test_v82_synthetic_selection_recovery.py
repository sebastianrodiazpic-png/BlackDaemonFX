from types import SimpleNamespace

from app.main import _recover_empty_synthetic_selection
from database.repository import TradingRepository
from strategy.execution.live_trading_engine import LiveTradingEngine


def test_empty_synthetic_profile_is_recovered_for_synthetic_coordinator(tmp_path):
    repo = TradingRepository(db_path=tmp_path / "v82.db")
    repo.save_instrument_selection_profile([], selection_profile="SYNTHETICS")
    catalog = {
        "boom": ["Boom 500 Index"],
        "volatility": ["Volatility 90 Index"],
        "forex": ["EURUSD"],
        "orb_ny_gold": ["XAUUSD"],
    }
    result = _recover_empty_synthetic_selection(repo, catalog, ["BOOM", "VOLATILITY"])
    assert result is not None
    assert repo.latest_instrument_selection_profile("SYNTHETICS")["selected_symbols"] == [
        "Boom 500 Index", "Volatility 90 Index"
    ]


def test_nonempty_synthetic_profile_is_preserved(tmp_path):
    repo = TradingRepository(db_path=tmp_path / "v82.db")
    original = repo.save_instrument_selection_profile(
        ["Boom 500 Index"], selection_profile="SYNTHETICS"
    )
    result = _recover_empty_synthetic_selection(
        repo, {"boom": ["Boom 500 Index", "Boom 1000 Index"]}, ["BOOM"]
    )
    assert result is None
    current = repo.latest_instrument_selection_profile("SYNTHETICS")
    assert current["selected_symbols"] == ["Boom 500 Index"]
    assert current["version"] == original["version"]


def test_empty_cycle_is_reported_as_degraded(tmp_path):
    repo = TradingRepository(db_path=tmp_path / "v82.db")
    engine = object.__new__(LiveTradingEngine)
    engine.repository = repo
    engine.config = SimpleNamespace(bot_profile="BOOM", magic=26082101, source="DEMO")
    engine._persist_audit_event(
        "DAEMON_CYCLE_START", cycle_number=1, payload={"symbols_count": 0}
    )
    state = next(
        row for row in repo.worker_runtime_states(source="DEMO")
        if row["bot_profile"] == "BOOM"
    )
    assert state["status"] == "DEGRADED_NO_SYMBOLS"
    assert state["last_action"] == "EMPTY_CYCLE"


def test_forex_without_new_m5_bar_is_waiting_not_degraded(tmp_path):
    repo = TradingRepository(db_path=tmp_path / "v83.db")
    engine = object.__new__(LiveTradingEngine)
    engine.repository = repo
    engine.config = SimpleNamespace(bot_profile="FOREX_1", magic=26082201, source="DEMO")
    engine._persist_audit_event(
        "DAEMON_CYCLE_START",
        cycle_number=12,
        payload={
            "symbols_count": 0,
            "selected_symbols_count": 9,
            "runtime_state": "WAITING_NEW_M5_BAR",
        },
    )
    state = next(
        row for row in repo.worker_runtime_states(source="DEMO")
        if row["bot_profile"] == "FOREX_1"
    )
    assert state["status"] == "WAITING_NEW_M5_BAR"
    assert state["current_symbol"] is None


def test_forex_without_candles_reports_data_wait(tmp_path):
    repo = TradingRepository(db_path=tmp_path / "v83.db")
    engine = object.__new__(LiveTradingEngine)
    engine.repository = repo
    engine.config = SimpleNamespace(bot_profile="FOREX_1", magic=26082201, source="DEMO")
    engine._persist_audit_event(
        "DAEMON_CYCLE_START",
        cycle_number=13,
        payload={
            "symbols_count": 0,
            "selected_symbols_count": 9,
            "runtime_state": "WAITING_FOREX_DATA",
        },
    )
    state = next(
        row for row in repo.worker_runtime_states(source="DEMO")
        if row["bot_profile"] == "FOREX_1"
    )
    assert state["status"] == "WAITING_FOREX_DATA"
