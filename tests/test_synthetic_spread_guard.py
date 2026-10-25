"""Tope de spread / distancia al SL en sintéticos (por defecto 2%).

Replay fiel ICT 365d: el R/trade empeora de forma monótona con spread/SL (p<0.002),
así que se bloquean las entradas en las que el spread consume más del 2% del riesgo.
"""
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace

import pytest

from strategy.execution.live_trading_engine import LiveTradingConfig, LiveTradingEngine


def make_engine(bid, ask, profile="VOLATILITY_1", **cfg):
    engine = object.__new__(LiveTradingEngine)
    engine.config = LiveTradingConfig(bot_profile=profile, **cfg)
    engine.executor = SimpleNamespace(get_current_tick=lambda _s: {
        "bid": bid, "ask": ask, "time": datetime.now(timezone.utc)})
    engine.audits = []
    engine._persist_audit_event = lambda event, **kw: engine.audits.append((event, kw))
    return engine


def test_default_ratio_is_two_percent():
    assert LiveTradingConfig().synthetic_spread_guard_enabled is True
    assert LiveTradingConfig().synthetic_spread_max_risk_ratio == pytest.approx(0.02)


def test_buy_within_limit_is_allowed_and_audited():
    # BUY entra al ask 100.10; SL 95.10 -> distancia 5.0; spread 0.10 -> 2.0% (límite inclusivo)
    engine = make_engine(100.0, 100.10)
    assert engine._synthetic_spread_gate("Volatility 75 Index", "BUY", 95.10) is None
    event, kw = engine.audits[-1]
    assert event == "SYNTHETIC_EXECUTION_SPREAD" and kw["action"] == "ALLOWED"
    assert kw["payload"]["spread_risk_ratio"] == pytest.approx(0.02)


def test_sell_above_limit_is_blocked():
    # SELL entra al bid 100.0; SL 102.0 -> distancia 2.0; spread 0.10 -> 5%
    engine = make_engine(100.0, 100.10)
    blocked = engine._synthetic_spread_gate("Crash 500 Index", "SELL", 102.0)
    assert blocked["action"] == "SYNTHETIC_SPREAD_TO_SL_EXCEEDED"
    assert blocked["spread_audit"]["spread_risk_ratio"] == pytest.approx(0.05)
    assert engine.audits[-1][1]["action"] == "BLOCKED"


def test_non_synthetic_and_disabled_are_ignored():
    engine = make_engine(1.1000, 1.1010)
    assert engine._synthetic_spread_gate("EURUSD", "BUY", 1.1005) is None
    assert engine.audits == []
    disabled = make_engine(100.0, 101.0, synthetic_spread_guard_enabled=False)
    assert disabled._synthetic_spread_gate("Boom 500 Index", "BUY", 100.5) is None


def test_configurable_ratio_and_env_override(monkeypatch):
    engine = make_engine(100.0, 100.10, synthetic_spread_max_risk_ratio=0.06)
    assert engine._synthetic_spread_gate("Jump 75 Index", "SELL", 102.0) is None  # 5% <= 6%
    # La variable de entorno se lee al importar: se comprueba en un proceso aparte para no recargar el motor.
    monkeypatch.setenv("DAEMONBLACKFX_SYNTHETIC_SPREAD_MAX_SL_RATIO", "0.01")
    out = subprocess.run(
        [sys.executable, "-c", "from strategy.execution.live_trading_engine import LiveTradingConfig as C;"
                               "print(C().synthetic_spread_max_risk_ratio)"],
        cwd=str(Path(__file__).resolve().parents[1]), capture_output=True, text=True, timeout=300)
    assert out.returncode == 0, out.stderr[-500:]
    assert float(out.stdout.strip().splitlines()[-1]) == pytest.approx(0.01)


def test_unavailable_quote_does_not_block():
    engine = make_engine(100.0, 100.10)
    engine.executor = SimpleNamespace(get_current_tick=lambda _s: (_ for _ in ()).throw(RuntimeError("no tick")))
    assert engine._synthetic_spread_gate("Step Index 400", "BUY", 99.0) is None
    assert engine.audits[-1][1]["reason"] == "SYNTHETIC_SPREAD_UNAVAILABLE_NOT_BLOCKING"


def test_execution_gate_applies_synthetic_guard():
    engine = make_engine(100.0, 100.10)
    blocked = engine._forex_execution_gate("Volatility 10 Index", "SELL", 102.0)
    assert blocked is not None and blocked["action"] == "SYNTHETIC_SPREAD_TO_SL_EXCEEDED"
    assert make_engine(100.0, 100.10)._forex_execution_gate("Volatility 10 Index", "SELL", 110.0) is None


# --- Multiplicador de riesgo en sintéticos (por defecto 1.0x: 1% total en 2 patas) ---

def test_default_synthetic_risk_multiplier_is_full_risk():
    assert LiveTradingConfig().synthetic_risk_multiplier == pytest.approx(1.0)


@pytest.mark.parametrize("symbol,mult,expected", [
    ("Volatility 75 Index", 0.5, 0.5),
    ("Boom 1000 Index", 0.25, 0.25),
    ("Step Index 400", 3.0, 1.0),      # acotado a 1.0: nunca aumenta el riesgo
    ("Jump 25 Index", 0.0, 0.1),       # acotado a 0.1
    ("EURUSD", 0.5, 1.0),              # no sintético: sin cambio
    ("XAUUSD", 0.5, 1.0),
])
def test_synthetic_risk_multiplier_scales_only_synthetics(symbol, mult, expected):
    engine = make_engine(100.0, 100.1, synthetic_risk_multiplier=mult)
    assert engine._apply_synthetic_risk_multiplier(symbol, 1.0) == pytest.approx(expected)


def test_synthetic_risk_multiplier_env_override(monkeypatch):
    monkeypatch.setenv("DAEMONBLACKFX_SYNTHETIC_RISK_MULT", "0.3")
    out = subprocess.run(
        [sys.executable, "-c", "from strategy.execution.live_trading_engine import LiveTradingConfig as C;"
                               "print(C().synthetic_risk_multiplier)"],
        cwd=str(Path(__file__).resolve().parents[1]), capture_output=True, text=True, timeout=300)
    assert out.returncode == 0, out.stderr[-500:]
    assert float(out.stdout.strip().splitlines()[-1]) == pytest.approx(0.3)


def test_execution_sizing_applies_synthetic_multiplier():
    import inspect
    source = inspect.getsource(LiveTradingEngine)
    apply_at = source.index("total_risk_percent = self._apply_synthetic_risk_multiplier(exact_symbol, total_risk_percent)")
    assert apply_at < source.index("total_risk_amount = risk_base_value * total_risk_percent / 100.0")
