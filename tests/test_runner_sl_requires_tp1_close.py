"""Contrato operativo: la pata RUNNER solo mueve su SL tras el cierre en ganancia de la pata TP1.

En la demo (sep-oct 2026) ~80 runners pasaron a BE con la pata TP1 aún abierta por tres rutas:
PRICE_REACHED_TRIGGER_RR (precio en 1R), CRASH_FAVORABLE_SPIKE_PROTECTIVE_BE (pico en Crash >= 0.40R)
y GOLD_NEW_YORK_OPEN_POSITIVE. La compuerta central bloquea cualquier cambio de SL del RUNNER hasta entonces.
"""
from types import SimpleNamespace

import pytest

from strategy.execution.live_trading_engine import LiveTradingConfig, LiveTradingEngine


def engine_with_sibling(sibling, **cfg):
    engine = object.__new__(LiveTradingEngine)
    engine.config = LiveTradingConfig(split_entries_enabled=True, **cfg)
    engine.repository = SimpleNamespace(get_trade_by_execution_key=lambda key: sibling)
    return engine


META = {"trade_leg": "RUNNER", "parent_execution_key": "DEMO:Crash 500 Index:H1:M15:M5:2026-10-19T10:00:00+00:00:SELL"}


def test_default_rule_enabled():
    assert LiveTradingConfig().runner_sl_requires_tp1_close is True


@pytest.mark.parametrize("sibling", [None, {"id": 1, "status": "OPEN", "result": ""},
                                     {"id": 1, "status": "CLOSED", "result": "LOSS", "realized_rr": -1.0}])
def test_runner_locked_while_tp1_not_closed_in_profit(sibling):
    engine = engine_with_sibling(sibling)
    lock = engine._runner_sl_locked_until_tp1({}, dict(META), "RUNNER")
    assert lock is not None and lock["reason"] == "RUNNER_SL_LOCKED_UNTIL_TP1_CLOSED"


def test_runner_unlocked_after_tp1_closed_in_profit():
    engine = engine_with_sibling({"id": 1, "status": "CLOSED", "result": "WIN", "realized_rr": 1.0})
    assert engine._runner_sl_locked_until_tp1({}, dict(META), "RUNNER") is None


@pytest.mark.parametrize("leg", ["TP1", "SINGLE", ""])
def test_rule_only_applies_to_runner_leg(leg):
    engine = engine_with_sibling(None)
    assert engine._runner_sl_locked_until_tp1({}, dict(META, trade_leg=leg), leg) is None


def test_rule_can_be_disabled():
    engine = engine_with_sibling(None, runner_sl_requires_tp1_close=False)
    assert engine._runner_sl_locked_until_tp1({}, dict(META), "RUNNER") is None


def test_guarded_move_stop_refuses_every_modification_while_locked():
    calls = []
    base = lambda **kw: calls.append(kw) or {"modified": True}
    guarded = LiveTradingEngine._guarded_move_stop(base, {"id": 7}, {"reason": "RUNNER_SL_LOCKED_UNTIL_TP1_CLOSED"})
    res = guarded(position_ticket="1", stop_loss=99.0, reason="crash_spike_protective_be")
    assert res["modified"] is False and res["reason"] == "RUNNER_SL_LOCKED_UNTIL_TP1_CLOSED"
    assert calls == []
    assert LiveTradingEngine._guarded_move_stop(base, {"id": 7}, None) is base


def test_monitor_wires_gate_before_any_stop_change():
    import inspect
    src = inspect.getsource(LiveTradingEngine._monitor_break_even_positions)
    i_gate = src.index("move_stop = self._guarded_move_stop(base_move_stop, trade, runner_locked)")
    assert i_gate < src.index("modification = move_stop(")
    assert "if runner_locked is not None:\n                    eligible = False" in src
