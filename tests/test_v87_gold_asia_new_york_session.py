from datetime import datetime, timezone
from types import SimpleNamespace

from app.main import BOT_PROFILES, FULL_MULTI_BOT_PROFILES, _selection_profile_for_bot
from strategy.execution.live_trading_engine import LiveTradingConfig, LiveTradingEngine


def _engine(profile="GOLD"):
    engine = object.__new__(LiveTradingEngine)
    engine.config = LiveTradingConfig(bot_profile=profile, orb_enabled=(profile == "ORB"))
    return engine


def test_gold_profile_is_independent_and_uses_orb_gold_selection():
    assert BOT_PROFILES["GOLD"]["magic"] == 26082029
    assert BOT_PROFILES["GOLD"]["mode"] == "gold-session-daemon"
    assert "GOLD" in FULL_MULTI_BOT_PROFILES
    assert _selection_profile_for_bot("GOLD") == "ORB"


def test_gold_window_opens_at_tokyo_0900_and_closes_at_new_york_0930_summer():
    engine = _engine()
    assert engine._gold_smc_session_state(datetime(2026, 9, 1, 0, 0, tzinfo=timezone.utc))["active"] is True
    assert engine._gold_smc_session_state(datetime(2026, 9, 1, 13, 29, tzinfo=timezone.utc))["active"] is True
    assert engine._gold_smc_session_state(datetime(2026, 9, 1, 13, 30, tzinfo=timezone.utc))["active"] is False


def test_gold_window_respects_new_york_winter_dst():
    engine = _engine()
    assert engine._gold_smc_session_state(datetime(2026, 12, 1, 14, 29, tzinfo=timezone.utc))["active"] is True
    assert engine._gold_smc_session_state(datetime(2026, 12, 1, 14, 30, tzinfo=timezone.utc))["active"] is False


def test_gold_entry_gate_does_not_affect_forex_or_synthetics():
    gold = _engine("GOLD")
    assert gold._gold_smc_entry_gate("XAUUSD", datetime(2026, 9, 1, 13, 29, tzinfo=timezone.utc)) is None
    assert gold._gold_smc_entry_gate("XAUUSD", datetime(2026, 9, 1, 13, 30, tzinfo=timezone.utc))["action"] == "GOLD_SMC_SESSION_CLOSED"
    assert _engine("FOREX_1")._gold_smc_entry_gate("EURUSD", datetime(2026, 9, 1, 15, 0, tzinfo=timezone.utc)) is None


def test_orb_detects_open_gold_smc_exposure():
    engine = _engine("ORB")
    engine.repository = SimpleNamespace(open_trades=lambda source: [{
        "id": 5, "instrument": "XAUUSD", "direction": "BUY",
        "entry_price": 2400.0, "stop_loss": 2390.0,
        "broker_position_ticket": "500",
        "details": {"metadata": {"bot_profile": "GOLD", "daemon_magic": 26082029}},
    }])
    exposure = engine._gold_smc_exposure_open()
    assert exposure["trade_id"] == 5
    assert exposure["break_even_confirmed"] is False
