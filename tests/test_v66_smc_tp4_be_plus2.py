from types import SimpleNamespace
import pandas as pd
import strategy.execution.live_trading_engine as live_mod
from strategy.execution.live_trading_engine import LiveTradingConfig, LiveTradingEngine
from strategy.execution.runner_extension_manager import RunnerExtensionDecision


class Repo:
    def __init__(self):
        self.updates=[]
        self.runner={
            "id":1,"broker_position_ticket":"123","instrument":"TEST","direction":"BUY",
            "stop_loss":90.0,"take_profit":140.0,
            "details":{"metadata":{
                "initial_stop_loss":90.0,
                "trade_leg":"RUNNER",
                "parent_execution_key":"TEST:SETUP:BUY",
                "strategy_name":"SMC",
                "break_even_activated":False,
            }}
        }
        self.tp1={"id":2,"status":"CLOSED","result":"WIN","realized_rr":1.0,"exit_price":110.0}
    def open_trades(self, source=None): return [self.runner]
    def get_trade_by_execution_key(self,key):
        return self.tp1 if key=="TEST:SETUP:BUY:TP1" else None
    def update_trade(self,trade_id,payload):
        self.updates.append((trade_id,payload))
        if trade_id==1:
            self.runner.update({k:v for k,v in payload.items() if k!="details"})
            if "details" in payload: self.runner["details"]=payload["details"]


class Provider:
    connector=SimpleNamespace()
    def get_candles(self,symbol,timeframe,count=80):
        return pd.DataFrame([
            {"time":pd.Timestamp("2026-08-31T12:00:00Z")+pd.Timedelta(minutes=5*i),
             "open":100+i,"high":101+i,"low":99+i,"close":100.8+i}
            for i in range(20)
        ])


class Broker:
    def __init__(self):
        self.sl=90.0
        self.tp=140.0
        self.current=106.0
    def get_symbol_constraints(self,symbol):
        return {"point":0.01,"tick_size":0.01,"digits":2}
    def get_position(self,ticket):
        return SimpleNamespace(ticket=ticket,price_open=100.0,price_current=self.current,sl=self.sl,tp=self.tp)


class TradeExecutor:
    def __init__(self,broker):
        self.broker=broker; self.moves=[]; self.closes=[]
    def move_stop_loss(self,position_ticket,stop_loss,take_profit=None,reason=""):
        self.moves.append((position_ticket,float(stop_loss),float(take_profit or 0),reason))
        self.broker.sl=float(stop_loss)
        if take_profit is not None: self.broker.tp=float(take_profit)
        return {"modified":True}
    def close_position(self,position_ticket,exit_price=None,reason="manual_close"):
        self.closes.append((position_ticket,reason))
        return {"closed":True}


def _engine(repo=None):
    repo=repo or Repo()
    broker=Broker()
    engine=LiveTradingEngine(
        provider=Provider(), repository=repo,
        config=LiveTradingConfig(
            execution_enabled=True,
            split_entries_enabled=True,
            split_entry_risk_fraction=.5,
            first_target_rr=1.0,
            second_target_rr=2.0,
            break_even_enabled=True,
            break_even_trigger_rr=1.0,
            break_even_offset_points=2,
            runner_extension_enabled=True,
            smc_runner_max_target_rr=4.0,
            smc_runner_tp3_guard_trigger_rr=2.5,
            smc_runner_tp3_guard_lock_rr=2.0,
            smc_runner_tp4_guard_trigger_rr=3.5,
            smc_runner_tp4_guard_lock_rr=3.0,
        ),
        executor=broker,
    )
    tx=TradeExecutor(broker)
    engine.lifecycle_manager=SimpleNamespace(trade_executor=tx)
    return engine,repo,broker,tx


def test_smc_configuration_is_half_half_and_tp4_cap():
    cfg=LiveTradingConfig()
    assert cfg.split_entries_enabled is True
    assert cfg.split_entry_risk_fraction == .5
    assert cfg.first_target_rr == 1.0
    assert cfg.second_target_rr == 2.0
    assert cfg.smc_runner_max_target_rr == 4.0
    assert cfg.break_even_offset_points == 2


def test_tp1_close_immediately_protects_runner_at_be_plus_two_points():
    engine,repo,broker,tx=_engine()
    # precio retrocedido a 0.6R; TP1 cerrado demuestra que 1R ya fue alcanzado.
    broker.current=106.0
    result=engine._monitor_break_even_positions()
    assert result["activated"] == 1
    assert broker.sl == 100.02
    assert tx.moves[0][1] == 100.02
    assert repo.runner["details"]["metadata"]["break_even_activation_reason"] == "TP1_CLOSED_IN_PROFIT"


def test_smc_3_5r_guard_locks_3r_while_targeting_4r():
    engine,repo,broker,tx=_engine()
    broker.current=135.5
    broker.sl=120.0
    position=broker.get_position(123)
    trade=repo.runner
    metadata=dict(trade["details"]["metadata"])
    metadata["runner_extension_completed_stages"]=[
        "2R_TO_3R","SMC_TP3_GUARD_2R","3R_TO_4R"
    ]
    metadata["runner_extension_stage"]="EXTENDED_TO_4R"
    result=engine._manage_runner_extension(
        trade=trade, position=position, metadata=metadata,
        initial_stop_loss=90.0, current_rr=3.55,
        move_stop=tx.move_stop_loss,
    )
    assert result["stage"] == "SMC_TP4_GUARD_3R"
    assert result["profit_lock_rr"] == 3.0
    assert broker.sl == 130.0
    assert broker.tp == 140.0
    assert metadata["runner_extension_stage"] == "PROTECTED_FOR_TP4"


def test_smc_at_3r_evaluates_before_seeking_tp4(monkeypatch):
    engine,repo,broker,tx=_engine()
    broker.current=130.5
    broker.sl=120.0
    position=broker.get_position(123)
    trade=repo.runner
    metadata=dict(trade["details"]["metadata"])
    metadata["runner_extension_completed_stages"]=["2R_TO_3R","SMC_TP3_GUARD_2R"]
    monkeypatch.setattr(
        live_mod,"evaluate_runner_continuation",
        lambda *a,**k: RunnerExtensionDecision(True,"CONTINUACION_TP4",{})
    )
    result=engine._manage_runner_extension(
        trade=trade, position=position, metadata=metadata,
        initial_stop_loss=90.0,current_rr=3.05,
        move_stop=tx.move_stop_loss,
    )
    assert result["stage"] == "3R_TO_4R"
    assert result["extended"] is True
    assert broker.sl == 120.0
    assert broker.tp == 140.0
