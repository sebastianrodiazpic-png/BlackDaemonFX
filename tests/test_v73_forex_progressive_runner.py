from types import SimpleNamespace
import pandas as pd
import strategy.execution.live_trading_engine as live_mod
from strategy.execution.live_trading_engine import LiveTradingConfig, LiveTradingEngine
from strategy.execution.runner_extension_manager import RunnerExtensionDecision


class Repo:
    def __init__(self):
        self.updates=[]
    def update_trade(self, trade_id, payload):
        self.updates.append((trade_id, payload))


class Provider:
    def get_candles(self, symbol, timeframe, count=80):
        return pd.DataFrame([
            {
                "time": pd.Timestamp("2026-09-01T12:00:00Z")+pd.Timedelta(minutes=5*i),
                "open":100+i,"high":101+i,"low":99+i,"close":100.8+i
            }
            for i in range(20)
        ])


class PositionExecutor:
    def __init__(self, position):
        self.position=position
    def get_position(self, ticket):
        return self.position
    def get_symbol_constraints(self, symbol):
        return {"point":0.00001,"tick_size":0.00001,"digits":5}


class TradeExecutor:
    def __init__(self, position):
        self.position=position
        self.moves=[]
        self.closes=[]
    def move_stop_loss(self, position_ticket, stop_loss, take_profit=None, reason=""):
        self.moves.append((position_ticket,float(stop_loss),float(take_profit),reason))
        self.position.sl=float(stop_loss)
        self.position.tp=float(take_profit)
        return {"modified":True}
    def close_position(self, position_ticket, exit_price=None, reason="manual_close"):
        self.closes.append((position_ticket,reason))
        return {"closed":True,"position_ticket":position_ticket,"reason":reason}


def _engine():
    pos=SimpleNamespace(price_open=1.10000,price_current=1.12000,sl=1.10002,tp=1.14000)
    engine=object.__new__(LiveTradingEngine)
    engine.config=LiveTradingConfig(
        bot_profile="FOREX_1",
        runner_extension_enabled=True,
        forex_runner_initial_target_rr=2.0,
        forex_runner_tp3_lock_rr=1.0,
        forex_runner_tp4_pre_eval_lock_rr=2.0,
        forex_runner_tp4_lock_rr=2.5,
        forex_runner_max_target_rr=4.0,
        forex_runner_broker_safety_target_rr=4.0,
    )
    engine.provider=Provider()
    engine.repository=Repo()
    engine.executor=PositionExecutor(pos)
    tx=TradeExecutor(pos)
    engine.lifecycle_manager=SimpleNamespace(trade_executor=tx)
    engine._break_even_price_tolerance=lambda symbol,entry: 1e-8
    return engine,pos,tx


def _trade():
    return {
        "id":73,
        "broker_position_ticket":"7300",
        "instrument":"EURUSD",
        "direction":"BUY",
        "details":{"metadata":{
            "trade_leg":"RUNNER",
            "initial_stop_loss":1.09000,
            "strategy_name":"SMC",
            "bot_profile":"FOREX_1",
            "runner_initial_target_rr":2.0,
            "runner_logical_target_rr":2.0,
            "runner_broker_safety_target_rr":4.0,
        }},
    }


def test_forex_runner_config_starts_at_tp2():
    cfg=LiveTradingConfig()
    assert cfg.forex_runner_initial_target_rr == 2.0
    assert cfg.second_target_rr == 2.0


def test_forex_runner_never_extends_past_tp2_even_if_extension_is_enabled(monkeypatch):
    engine,pos,tx=_engine()
    trade=_trade()
    metadata=dict(trade["details"]["metadata"])
    monkeypatch.setattr(
        live_mod,"evaluate_runner_continuation",
        lambda *a,**k: RunnerExtensionDecision(True,"CONTINUACION_TP3",{})
    )
    result=engine._manage_runner_extension(
        trade=trade,position=pos,metadata=metadata,
        initial_stop_loss=1.09000,current_rr=2.05,
        move_stop=tx.move_stop_loss,
    )
    assert result["managed"] is False
    assert result["reason"] == "FOREX_FIXED_TP2_TARGET"
    assert tx.moves == []
    assert tx.closes == []


def test_source_builds_forex_runner_with_fixed_tp2():
    from pathlib import Path
    root=Path(__file__).resolve().parents[1]
    text=(root/"strategy"/"execution"/"live_trading_engine.py").read_text(encoding="utf-8")
    assert 'result["reason"] = "FOREX_FIXED_TP2_TARGET"' in text
