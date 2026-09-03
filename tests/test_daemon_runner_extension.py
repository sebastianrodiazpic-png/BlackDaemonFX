
from types import SimpleNamespace

import pandas as pd

import strategy.execution.live_trading_engine as live_mod
from strategy.execution.live_trading_engine import LiveTradingConfig, LiveTradingEngine
from strategy.execution.runner_extension_manager import RunnerExtensionDecision


class Repo:
    def __init__(self):
        self.updates = []

    def update_trade(self, trade_id, payload):
        self.updates.append((trade_id, payload))


class Provider:
    def get_candles(self, symbol, timeframe, count=80):
        return pd.DataFrame([
            {
                "time": pd.Timestamp("2026-08-30T12:00:00Z") + pd.Timedelta(minutes=5*i),
                "open": 100+i, "high": 101+i, "low": 99+i, "close": 100.8+i,
            }
            for i in range(20)
        ])


class PositionExecutor:
    def __init__(self, position):
        self.position = position

    def get_position(self, ticket):
        return self.position

    def get_symbol_constraints(self, symbol):
        return {"point": 0.01, "tick_size": 0.01, "digits": 2}


class TradeExecutor:
    def __init__(self, position):
        self.position = position
        self.moves = []
        self.closes = []

    def move_stop_loss(self, position_ticket, stop_loss, take_profit=None, reason=""):
        self.moves.append((position_ticket, stop_loss, take_profit, reason))
        self.position.sl = float(stop_loss)
        self.position.tp = float(take_profit)
        return {"modified": True}

    def close_position(self, position_ticket, exit_price=None, reason="manual_close"):
        self.closes.append((position_ticket, reason))
        return {"closed": True, "position_ticket": position_ticket, "reason": reason}


def _engine():
    position = SimpleNamespace(
        price_open=100.0,
        price_current=120.5,
        sl=100.02,
        tp=140.0,
    )
    engine = object.__new__(LiveTradingEngine)
    engine.config = LiveTradingConfig(
        execution_enabled=True,
        runner_extension_enabled=True,
        runner_extension_first_trigger_rr=2.0,
        runner_extension_first_lock_rr=1.0,
        runner_extension_second_trigger_rr=3.0,
        runner_extension_second_lock_rr=2.0,
        runner_extension_max_target_rr=4.0,
    )
    engine.provider = Provider()
    engine.repository = Repo()
    engine.executor = PositionExecutor(position)
    trade_executor = TradeExecutor(position)
    engine.lifecycle_manager = SimpleNamespace(trade_executor=trade_executor)
    return engine, position, trade_executor


def _trade(strategy_name="SMC"):
    return {
        "id": 77,
        "broker_position_ticket": "1234",
        "instrument": "Volatility 75 Index",
        "direction": "BUY",
        "details": {
            "metadata": {
                "trade_leg": "RUNNER",
                "initial_stop_loss": 90.0,
                "strategy_name": strategy_name,
            }
        },
    }


def test_at_2r_profit_is_locked_at_1r_before_extending(monkeypatch):
    engine, position, trade_executor = _engine()
    monkeypatch.setattr(
        live_mod,
        "evaluate_runner_continuation",
        lambda *a, **k: RunnerExtensionDecision(
            True, "CONTINUACION_ESTRUCTURAL_CONFIRMADA", {}
        ),
    )

    metadata = dict(_trade()["details"]["metadata"])
    result = engine._manage_runner_extension(
        trade=_trade(),
        position=position,
        metadata=metadata,
        initial_stop_loss=90.0,
        current_rr=2.05,
        move_stop=trade_executor.move_stop_loss,
    )

    assert result["extended"] is True
    assert result["stage"] == "2R_TO_3R"
    assert position.sl == 110.0
    assert position.tp == 140.0
    assert metadata["runner_extension_stage"] == "EXTENDED_TO_3R"
    assert metadata["runner_profit_lock_rr"] == 1.0


def test_at_2r_no_continuation_closes_runner_after_locking_profit(monkeypatch):
    engine, position, trade_executor = _engine()
    monkeypatch.setattr(
        live_mod,
        "evaluate_runner_continuation",
        lambda *a, **k: RunnerExtensionDecision(
            False, "CHOCH_CONTRARIO_RECIENTE", {}
        ),
    )

    metadata = dict(_trade()["details"]["metadata"])
    result = engine._manage_runner_extension(
        trade=_trade(),
        position=position,
        metadata=metadata,
        initial_stop_loss=90.0,
        current_rr=2.10,
        move_stop=trade_executor.move_stop_loss,
    )

    assert position.sl == 110.0
    assert result["closed"] is True
    assert trade_executor.closes
    assert "CHOCH_CONTRARIO_RECIENTE" in metadata["runner_exit_reason"]


def test_at_3r_profit_lock_advances_to_2r(monkeypatch):
    engine, position, trade_executor = _engine()
    position.price_current = 130.5
    orb_trade = _trade("ORB_NEW_YORK")
    metadata = dict(orb_trade["details"]["metadata"])
    metadata["runner_extension_completed_stages"] = ["2R_TO_3R"]
    metadata["runner_extension_stage"] = "EXTENDED_TO_3R"
    position.sl = 110.0

    monkeypatch.setattr(
        live_mod,
        "evaluate_runner_continuation",
        lambda *a, **k: RunnerExtensionDecision(
            True, "CONTINUACION_ESTRUCTURAL_CONFIRMADA", {}
        ),
    )

    result = engine._manage_runner_extension(
        trade=orb_trade,
        position=position,
        metadata=metadata,
        initial_stop_loss=90.0,
        current_rr=3.05,
        move_stop=trade_executor.move_stop_loss,
    )

    assert result["stage"] == "3R_TO_4R"
    assert position.sl == 120.0
    assert metadata["runner_extension_stage"] == "EXTENDED_TO_4R"
    assert metadata["runner_profit_lock_rr"] == 2.0
