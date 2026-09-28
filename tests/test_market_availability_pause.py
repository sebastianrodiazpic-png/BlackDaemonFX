from datetime import datetime, timezone, timedelta
from types import SimpleNamespace
import pytest
from strategy.execution.live_trading_engine import LiveTradingEngine, LiveTradingConfig

@pytest.mark.parametrize("profile",["FOREX_1","GOLD"])
def test_calendar_restrictions_disabled(profile):
    e=object.__new__(LiveTradingEngine)
    e.config=LiveTradingConfig(bot_profile=profile)
    assert e._analysis_session_status("2026-09-20T22:00:00Z")["active"]
    assert not e.config.forex_rollover_guard_enabled
    assert not e.config.gold_smc_session_enabled


def test_quote_availability_filters_and_caches():
    e=object.__new__(LiveTradingEngine)
    calls=[]
    def tick(symbol):
        calls.append(symbol)
        return {"time":datetime.now(timezone.utc)-timedelta(minutes=10 if symbol=="CLOSED" else 0),"bid":100,"ask":101}
    e.executor=SimpleNamespace(get_current_tick=tick)
    available,unavailable=e._available_market_symbols(["OPEN","CLOSED"])
    assert available==["OPEN"] and "CLOSED" in unavailable
    e._available_market_symbols(["OPEN","CLOSED"])
    assert len(calls)==2


def test_all_unavailable_pauses_worker_without_candle_reads():
    e=object.__new__(LiveTradingEngine)
    e.config=LiveTradingConfig(bot_profile="GOLD")
    e.executor=SimpleNamespace(get_current_tick=lambda s:{"time":None})
    assert e._forex_due_symbols(["XAUUSD"])==[]
    assert e._analysis_session_diagnostics["state"]=="OUTSIDE_SESSION"
    assert "MT5" in e._analysis_session_diagnostics["reason"]


def test_availability_resumes_after_cache_expiry():
    e=object.__new__(LiveTradingEngine)
    e.executor=SimpleNamespace(get_current_tick=lambda s:{"time":datetime.now(timezone.utc),"bid":1,"ask":2})
    e._market_availability_cache=(("EURUSD",),datetime.now(timezone.utc)-timedelta(seconds=61),[],{"EURUSD":"closed"})
    assert e._available_market_symbols(["EURUSD"])[0]==["EURUSD"]
