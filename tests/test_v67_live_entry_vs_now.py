from types import SimpleNamespace
from pathlib import Path

from strategy.execution.live_trading_engine import LiveTradingConfig, LiveTradingEngine


def test_current_strategy_view_normalizes_waiting_state():
    analysis={
        "valid":False,
        "action":"NO_M15_SETUP",
        "state":"NO_M15_SETUP",
        "direction":"BUY",
        "reason":"NO_DIRECTIONAL_M15_SETUP",
        "h1":{"context":{"trend":"BULLISH"}},
        "m15":{"setup":None},
        "m5":None,
    }
    view=LiveTradingEngine._current_strategy_view_from_analysis(analysis)
    assert view["decision"]=="NO_M15_SETUP"
    assert view["state"]=="NO_M15_SETUP"
    assert view["direction"]=="BUY"
    assert view["h1_trend"]=="BULLISH"
    assert view["evaluated_at"]


def test_current_strategy_view_extracts_live_signal_confirmations():
    analysis={
        "valid":True,
        "action":"READY_TO_ENTER",
        "direction":"BUY",
        "h1":{"context":{"trend":"BULLISH"}},
        "m15":{"setup":{"zone":"DISCOUNT","structure_break_type":"BOS"}},
        "signal":{
            "direction":"BUY",
            "confirmation_decision":"ADAPTIVE_80_CONFIRMED",
            "trade_score":91,
            "confirmation_percentage":87.5,
            "passed_confirmations":["liquidity_sweep","micro_structure"],
            "missing_confirmations":["harmonic_confirmation"],
            "chart_pattern_confirmed":True,
            "chart_pattern_name":"DOUBLE_BOTTOM",
            "chart_pattern_strength":.81,
        },
    }
    view=LiveTradingEngine._current_strategy_view_from_analysis(analysis)
    assert view["decision"]=="ADAPTIVE_80_CONFIRMED"
    assert view["score"]==91
    assert view["confirmation_percentage"]==87.5
    assert "liquidity_sweep" in view["passed"]
    assert view["chart_pattern_name"]=="DOUBLE_BOTTOM"
    assert view["structure_break"]=="BOS"
    assert view["zone"]=="DISCOUNT"


class Repo:
    def __init__(self):
        self.writes=[]
        self.trade={
            "id":11,
            "instrument":"Volatility 75 Index",
            "broker_position_ticket":"5001",
            "details":{"metadata":{
                "strategy_name":"SMC",
                "bot_profile":"VOLATILITY",
                "daemon_magic":26082103,
            }},
        }
    def open_trades(self,source=None):
        return [self.trade]
    def trade_visual_audits(self,source=None):
        return [{
            "trade_id":11,
            "latest_market":{"current_price":105.0,"current_rr":1.2},
            "entry_context":{"decision":"ENTRY_DO_NOT_CHANGE"},
        }]
    def upsert_trade_visual_audit(self,trade_id,**kwargs):
        self.writes.append((trade_id,kwargs))
    def save_audit_event(self,*a,**k):
        return None


class Analyzer:
    def analyze_symbol(self,symbol):
        return {
            "valid":False,
            "action":"WAITING_M5_CONFIRMATION",
            "state":"WAITING_M5_CONFIRMATION",
            "direction":"BUY",
            "reason":"WAITING_FOR_FRESH_M5",
            "h1":{"context":{"trend":"BULLISH"}},
            "m15":{"setup":{"zone":"DISCOUNT","structure_break_type":"BOS"}},
            "m5":None,
        }


def test_open_smc_position_is_reanalyzed_and_persisted_without_touching_entry():
    engine=object.__new__(LiveTradingEngine)
    engine.config=LiveTradingConfig(
        source="DEMO",
        bot_profile="VOLATILITY",
        magic=26082103,
        current_strategy_refresh_seconds=2.0,
    )
    repo=Repo()
    engine.repository=repo
    engine.multi_timeframe=Analyzer()
    engine._last_current_strategy_refresh_monotonic=0.0
    engine._trade_owned_by_current_bot=lambda trade: True
    engine._persist_audit_event=lambda *a,**k: None

    result=engine._refresh_current_strategy_views()
    assert result["updated"]==1
    _,kwargs=repo.writes[-1]
    latest=kwargs["latest_market"]
    assert latest["current_price"]==105.0
    assert latest["current_rr"]==1.2
    assert latest["current_strategy_view"]["decision"]=="WAITING_M5_CONFIRMATION"
    assert "entry_context" not in kwargs


def test_dashboard_prioritizes_persisted_current_strategy_view():
    root=Path(__file__).resolve().parents[1]
    text=(root/"dashboard"/"realtime_dashboard.py").read_text(encoding="utf-8")
    assert 'market.get("current_strategy_view")' in text
    assert 'position["latest_strategy_view"] = dict(persisted_current)' in text
    assert "Actualizado ${new Date(v.evaluated_at)" in text


def test_live_refresh_is_independent_from_30_second_chart_persistence():
    root=Path(__file__).resolve().parents[1]
    text=(root/"strategy"/"execution"/"live_trading_engine.py").read_text(encoding="utf-8")
    assert "current_strategy_refresh_seconds: float = 10.0" in text
    assert "current_strategy = self._refresh_current_strategy_views()" in text
    assert 'monitor_result["current_strategy"] = current_strategy' in text
