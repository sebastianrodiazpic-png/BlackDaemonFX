
from types import SimpleNamespace
import pytest
from strategy.execution.live_trading_engine import LiveTradingEngine, LiveTradingConfig
from strategy.orb.new_york_orb import NewYorkORBStrategy

def engine(profile):
    e = object.__new__(LiveTradingEngine)
    e.config = LiveTradingConfig(bot_profile=profile, gold_smc_session_enabled=True, forex_rollover_guard_enabled=True)
    e._available_market_symbols = lambda symbols: (symbols, {})
    e.orb_strategy = NewYorkORBStrategy(None)
    return e

@pytest.mark.parametrize("profile,now,active,next_open", [
    ("ORB","2026-09-15T13:00:00Z",False,"2026-09-15T13:30:00+00:00"),
    ("ORB","2026-09-15T13:30:00Z",True,None),
    ("ORB","2026-09-15T20:00:00Z",False,"2026-09-16T13:30:00+00:00"),
    ("ORB","2026-09-19T15:00:00Z",False,"2026-09-21T13:30:00+00:00"),
    ("ORB","2026-11-02T14:00:00Z",False,"2026-11-02T14:30:00+00:00"),
    ("FOREX_1","2026-09-15T21:00:00Z",False,"2026-09-16T00:00:00+00:00"),
    ("FOREX_1","2026-09-16T00:00:00Z",True,None),
    ("GOLD","2026-09-15T15:00:00Z",False,"2026-09-16T00:00:00+00:00"),
    ("GOLD","2026-09-16T00:00:00Z",True,None),
    ("VOLATILITY_1","2026-09-19T15:00:00Z",True,None),
])
def test_calendar(profile,now,active,next_open):
    s=engine(profile)._analysis_session_status(now)
    assert s["active"] is active
    assert s["next_activation"] == next_open

def test_closed_session_never_fetches_candles():
    e=engine("FOREX_1")
    e._analysis_session_status=lambda: {"state":"OUTSIDE_SESSION","active":False,"next_activation":"tomorrow"}
    e.provider=SimpleNamespace(get_candles=lambda *a,**k: pytest.fail("Unexpected candles"))
    assert e._forex_due_symbols(["EURUSD"]) == []
    assert e._forex_scheduler_diagnostics["session"]["state"] == "OUTSIDE_SESSION"

def test_warmup_one_symbol_per_cycle_once_and_no_execution():
    e=engine("GOLD")
    s=e._analysis_session_status("2026-09-15T23:58:00Z")
    assert s["state"]=="SESSION_WARMUP" and not s["active"]
    e._analysis_session_status=lambda:s
    calls=[]
    cfg=SimpleNamespace(require_h4_h1_convergence=False,higher_timeframe="H4",higher_timeframe_candles=100,
        structure_timeframe="H1",structure_candles=100,confirmation_timeframe="M15",
        confirmation_candles=100,entry_timeframe="M5",entry_candles=100)
    e.multi_timeframe=SimpleNamespace(config=cfg,_get_stage_result=lambda *args:calls.append(args))
    for _ in range(3):
        assert e._forex_due_symbols(["XAUUSD","XAUUSDmicro"])==[]
    assert len(calls)==6
    assert all(call[1] != "H4" for call in calls)

def test_resume_clears_poll_boundary():
    e=engine("FOREX_1")
    e.config.forex_event_scheduler_enabled=False
    e._session_was_paused=True
    e._event_scheduler_next_poll_at="old"
    e._analysis_session_status=lambda:{"state":"ACTIVE","active":True}
    assert e._forex_due_symbols(["EURUSD"])==["EURUSD"]
    assert e._event_scheduler_next_poll_at is None
