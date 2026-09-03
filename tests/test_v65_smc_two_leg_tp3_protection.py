from types import SimpleNamespace

import pandas as pd
import strategy.execution.live_trading_engine as live_mod
from strategy.execution.live_trading_engine import LiveTradingConfig, LiveTradingEngine
from strategy.execution.runner_extension_manager import RunnerExtensionDecision


class Repo:
    def __init__(self):
        self.updates=[]
    def update_trade(self, trade_id, payload):
        self.updates.append((trade_id,payload))


class Provider:
    def get_candles(self, symbol, timeframe, count=80):
        return pd.DataFrame([
            {"time":pd.Timestamp("2026-08-31T12:00:00Z")+pd.Timedelta(minutes=5*i),
             "open":100+i,"high":101+i,"low":99+i,"close":100.8+i}
            for i in range(20)
        ])


class PositionExecutor:
    def __init__(self, position):
        self.position=position
    def get_position(self, ticket):
        return self.position
    def get_symbol_constraints(self, symbol):
        return {"point":0.01,"tick_size":0.01,"digits":2}


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
    pos=SimpleNamespace(price_open=100.0,price_current=120.5,sl=100.02,tp=130.0)
    engine=object.__new__(LiveTradingEngine)
    engine.config=LiveTradingConfig(
        execution_enabled=True,
        runner_extension_enabled=True,
        runner_extension_first_trigger_rr=2.0,
        runner_extension_first_lock_rr=1.0,
        runner_extension_second_trigger_rr=3.0,
        runner_extension_second_lock_rr=2.0,
        runner_extension_max_target_rr=4.0,
        smc_runner_max_target_rr=4.0,
        smc_runner_tp3_guard_trigger_rr=2.5,
        smc_runner_tp3_guard_lock_rr=2.0,
    )
    engine.provider=Provider()
    engine.repository=Repo()
    engine.executor=PositionExecutor(pos)
    tx=TradeExecutor(pos)
    engine.lifecycle_manager=SimpleNamespace(trade_executor=tx)
    return engine,pos,tx


def _trade():
    return {
        "id":91,
        "broker_position_ticket":"9100",
        "instrument":"Volatility 75 Index",
        "direction":"BUY",
        "details":{"metadata":{
            "trade_leg":"RUNNER",
            "initial_stop_loss":90.0,
            "strategy_name":"SMC",
        }},
    }


def test_smc_defaults_are_half_half_tp1_tp2_and_tp3_max():
    cfg=LiveTradingConfig()
    assert cfg.split_entries_enabled is True
    assert cfg.split_entry_risk_fraction == 0.50
    assert cfg.first_target_rr == 1.0
    assert cfg.second_target_rr == 2.0
    assert cfg.smc_runner_max_target_rr == 4.0
    assert cfg.smc_runner_tp3_guard_trigger_rr == 2.5
    assert cfg.smc_runner_tp3_guard_lock_rr == 2.0


def test_smc_at_2r_locks_1r_then_extends_only_to_tp3(monkeypatch):
    engine,pos,tx=_engine()
    monkeypatch.setattr(
        live_mod,"evaluate_runner_continuation",
        lambda *a,**k: RunnerExtensionDecision(True,"CONTINUACION_SMC_CONFIRMADA",{})
    )
    trade=_trade()
    metadata=dict(trade["details"]["metadata"])
    result=engine._manage_runner_extension(
        trade=trade,position=pos,metadata=metadata,
        initial_stop_loss=90.0,current_rr=2.05,
        move_stop=tx.move_stop_loss,
    )
    assert result["extended"] is True
    assert result["stage"] == "2R_TO_3R"
    assert result["target_rr"] == 4.0
    assert pos.sl == 110.0
    assert pos.tp == 140.0
    assert metadata["runner_profit_lock_rr"] == 1.0
    assert metadata["runner_extension_stage"] == "EXTENDED_TO_3R"


def test_smc_at_2r_without_continuation_closes_runner_after_profit_lock(monkeypatch):
    engine,pos,tx=_engine()
    monkeypatch.setattr(
        live_mod,"evaluate_runner_continuation",
        lambda *a,**k: RunnerExtensionDecision(False,"SIN_CONTINUACION_SMC",{})
    )
    trade=_trade()
    metadata=dict(trade["details"]["metadata"])
    result=engine._manage_runner_extension(
        trade=trade,position=pos,metadata=metadata,
        initial_stop_loss=90.0,current_rr=2.05,
        move_stop=tx.move_stop_loss,
    )
    assert pos.sl == 110.0
    assert result["closed"] is True
    assert tx.closes
    assert "SIN_CONTINUACION_SMC" in metadata["runner_exit_reason"]


def test_smc_between_tp2_and_tp3_advances_profit_lock_to_2r():
    engine,pos,tx=_engine()
    pos.price_current=125.5
    pos.sl=110.0
    trade=_trade()
    metadata=dict(trade["details"]["metadata"])
    metadata["runner_extension_completed_stages"]=["2R_TO_3R"]
    metadata["runner_extension_stage"]="EXTENDED_TO_3R"
    result=engine._manage_runner_extension(
        trade=trade,position=pos,metadata=metadata,
        initial_stop_loss=90.0,current_rr=2.55,
        move_stop=tx.move_stop_loss,
    )
    assert result["stage"] == "SMC_TP3_GUARD_2R"
    assert result["profit_lock_rr"] == 2.0
    assert pos.sl == 120.0
    assert pos.tp == 140.0
    assert metadata["runner_extension_stage"] == "PROTECTED_FOR_TP3"


def test_smc_at_3r_can_extend_to_tp4_with_2r_locked(monkeypatch):
    engine,pos,tx=_engine()
    pos.price_current=130.5
    pos.sl=120.0
    trade=_trade()
    metadata=dict(trade["details"]["metadata"])
    metadata["runner_extension_completed_stages"]=["2R_TO_3R","SMC_TP3_GUARD_2R"]
    metadata["runner_extension_stage"]="PROTECTED_FOR_TP3"
    monkeypatch.setattr(
        live_mod,"evaluate_runner_continuation",
        lambda *a,**k: RunnerExtensionDecision(True,"CONTINUACION_HACIA_TP4",{})
    )
    result=engine._manage_runner_extension(
        trade=trade,position=pos,metadata=metadata,
        initial_stop_loss=90.0,current_rr=3.05,
        move_stop=tx.move_stop_loss,
    )
    assert result["stage"] == "3R_TO_4R"
    assert result["extended"] is True
    assert result["target_rr"] == 4.0
    assert pos.sl == 120.0
    assert pos.tp == 140.0
    assert metadata["runner_extension_stage"] == "EXTENDED_TO_4R"


def test_smc_at_3r_without_continuation_closes_after_2r_lock(monkeypatch):
    engine,pos,tx=_engine()
    pos.price_current=130.5
    pos.sl=120.0
    trade=_trade()
    metadata=dict(trade["details"]["metadata"])
    metadata["runner_extension_completed_stages"]=["2R_TO_3R","SMC_TP3_GUARD_2R"]
    monkeypatch.setattr(
        live_mod,"evaluate_runner_continuation",
        lambda *a,**k: RunnerExtensionDecision(False,"SIN_CONTINUACION_TP4",{})
    )
    result=engine._manage_runner_extension(
        trade=trade,position=pos,metadata=metadata,
        initial_stop_loss=90.0,current_rr=3.05,
        move_stop=tx.move_stop_loss,
    )
    assert result["stage"] == "3R_TO_4R"
    assert result["closed"] is True
    assert pos.sl == 120.0
    assert tx.closes



def test_orb_keeps_tp4_cap():
    cfg=LiveTradingConfig()
    assert cfg.runner_extension_max_target_rr == 4.0
