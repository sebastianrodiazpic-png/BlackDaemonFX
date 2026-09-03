from pathlib import Path
from types import SimpleNamespace

from strategy.execution.live_trading_engine import LiveTradingConfig, LiveTradingEngine


class Repo:
    def __init__(self):
        self.calls=[]
    def upsert_trade_visual_audit(self, trade_id, **kwargs):
        self.calls.append((trade_id,kwargs))


def _engine(profile):
    e=object.__new__(LiveTradingEngine)
    e.config=LiveTradingConfig(bot_profile=profile, magic=123456)
    e.repository=Repo()
    e._current_strategy_view_cache={
        "XAUUSD":{"decision":"WAITING","evaluated_at":"2026-09-01T12:00:00+00:00"}
    }
    return e


def test_live_market_snapshot_persists_for_orb():
    e=_engine("ORB")
    result=e._persist_live_position_market_snapshots([{
        "trade_id":1,"ticket":"100","symbol":"XAUUSD","direction":"BUY",
        "current_price":4500.0,"current_rr":0.42,"current_stop_loss":4480.0,
    }])
    assert result["updated"]==1
    assert e.repository.calls
    payload=e.repository.calls[0][1]["latest_market"]
    assert payload["current_rr"]==0.42
    assert payload["telemetry_mode"]=="LIVE_POSITION_MONITOR"
    assert payload["current_strategy_view"]["decision"]=="WAITING"


def test_live_market_snapshot_persists_for_forex():
    e=_engine("FOREX_1")
    result=e._persist_live_position_market_snapshots([{
        "trade_id":2,"ticket":"200","symbol":"EURUSD","direction":"BUY",
        "current_price":1.12,"current_rr":0.8,
    }])
    assert result["updated"]==1
    assert e.repository.calls[0][1]["bot_profile"]=="FOREX_1"


def test_live_market_snapshot_persists_for_synthetic():
    e=_engine("BOOM")
    result=e._persist_live_position_market_snapshots([{
        "trade_id":3,"ticket":"300","symbol":"Boom 1000 Index","direction":"SELL",
        "current_price":1200.0,"current_rr":-0.2,
    }])
    assert result["updated"]==1
    assert e.repository.calls[0][1]["bot_profile"]=="BOOM"


def test_dashboard_prefers_current_strategy_view_from_trade_market():
    root=Path(__file__).resolve().parents[1]
    text=(root/"dashboard"/"realtime_dashboard.py").read_text(encoding="utf-8")
    assert "current_strategy_view = (" in text
    assert "latest = current_strategy_view" in text
    assert 'position["market_updated_at"]' in text


def test_monitor_persists_live_position_telemetry_each_pass():
    root=Path(__file__).resolve().parents[1]
    text=(root/"strategy"/"execution"/"live_trading_engine.py").read_text(encoding="utf-8")
    assert "_persist_live_position_market_snapshots(position_snapshots)" in text
    assert '"live_persistence": live_persistence' in text
