
from datetime import datetime, timezone
from strategy.execution.live_trading_engine import LiveTradingConfig, LiveTradingEngine

def _engine():
    e=object.__new__(LiveTradingEngine)
    e.config=LiveTradingConfig(
        execution_enabled=True,
        forex_rollover_guard_enabled=True,
        forex_new_entry_cutoff_hour=16,
        forex_new_entry_cutoff_minute=30,
        forex_force_flat_hour=16,
        forex_force_flat_minute=45,
        forex_tokyo_session_start_hour=9,
        forex_tokyo_session_start_minute=0,
    )
    return e

def test_forex_classifier_does_not_touch_synthetics_or_gold():
    e=_engine()
    assert e._is_forex_symbol("EURUSD")
    assert e._is_forex_symbol("GBPUSDm")
    assert not e._is_forex_symbol("Volatility 75 Index")
    assert not e._is_forex_symbol("XAUUSD")

def test_new_entries_blocked_from_1630_new_york():
    s=_engine()._forex_rollover_status(datetime(2026,8,31,20,30,tzinfo=timezone.utc))
    assert s["block_new_entries"] is True
    assert s["force_flat_now"] is False

def test_force_flat_from_1645_new_york():
    s=_engine()._forex_rollover_status(datetime(2026,8,31,20,45,tzinfo=timezone.utc))
    assert s["block_new_entries"] is True
    assert s["force_flat_now"] is True

def test_asian_and_london_hours_are_enabled_after_tokyo_open():
    s=_engine()._forex_rollover_status(datetime(2026,9,1,4,0,tzinfo=timezone.utc))
    assert s["block_new_entries"] is False

def test_cycle_restarts_exactly_at_tokyo_0900_summer():
    s=_engine()._forex_rollover_status(datetime(2026,9,1,0,0,tzinfo=timezone.utc))
    assert s["now_tokyo"].startswith("2026-09-01T09:00:00")
    assert s["block_new_entries"] is False
    assert s["force_flat_now"] is False

def test_cycle_restarts_exactly_at_tokyo_0900_winter():
    s=_engine()._forex_rollover_status(datetime(2026,12,1,0,0,tzinfo=timezone.utc))
    assert s["now_tokyo"].startswith("2026-12-01T09:00:00")
    assert s["block_new_entries"] is False
    assert s["force_flat_now"] is False

def test_dst_new_york_force_flat_still_works_in_winter():
    # NY UTC-5: 21:45 UTC = 16:45 NY.
    s=_engine()._forex_rollover_status(datetime(2026,12,1,21,45,tzinfo=timezone.utc))
    assert s["force_flat_now"] is True
    assert s["block_new_entries"] is True

def test_monday_before_tokyo_is_blocked():
    # Domingo 23:59 UTC = lunes 08:59 Tokio.
    s=_engine()._forex_rollover_status(datetime(2026,8,30,23,59,tzinfo=timezone.utc))
    assert s["block_new_entries"] is True

def test_friday_cutoff_stays_blocked_until_monday_tokyo():
    s=_engine()._forex_rollover_status(datetime(2026,9,5,12,0,tzinfo=timezone.utc))
    assert s["block_new_entries"] is True
