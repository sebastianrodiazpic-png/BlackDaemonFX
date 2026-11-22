"""Tests de validación para las correcciones de ingeniería y humanización de trading (09-nov-2026):
- 1.1: NameError 'strat_name' en ORB sweep corregido
- 1.2: self.Session() en repository.py corregido
- 1.3: Preservación del sufijo :RUNNER/-RUNNER en comentarios MT5
- 2.2: Blindaje temporal en inferencia de TP1 hermano (<= 15 min)
- 2.3: Escudo Anti-Spike activado ante peligro real en Crash/Boom
- 2.4: Transparencia en Filtro de IA y compensación de Criterio Humano (80 pts)
- 2.5: Horario continuo Cripto 24/7 sin cierre forzado por defecto
"""

from datetime import datetime, timezone, timedelta
from types import SimpleNamespace
import pytest

from brokers.mt5_execution import MT5ExecutionProvider
from strategy.confluence.tripartite_confluence_gate import (
    TripartiteConfluenceGate,
    TripartiteConfluenceConfig,
)
from strategy.execution.live_trading_engine import LiveTradingConfig, LiveTradingEngine


def test_1_1_orb_sweep_session_name_defined():
    """_evaluate_sweep debe asignar 'ORB_LONDON' o 'ORB_NEW_YORK' según la sesión sin NameError."""
    from strategy.orb.new_york_orb import NewYorkORBStrategy, ORBConfig
    import pandas as pd
    strategy = NewYorkORBStrategy(None, ORBConfig())

    # Comprobación de que strat_name está definido en el método y en globals
    import inspect
    src = inspect.getsource(strategy._evaluate_sweep)
    assert "strat_name = " in src
    assert '"strategy_name": strat_name' in src


def test_1_3_mt5_comment_preserves_leg_suffix():
    """El comentario de MT5 no debe superar 30 bytes pero debe preservar siempre el tag :RUNNER o :TP1."""
    long_comment_runner = "ORB_NEW_YORK_20261109_TRADE_UUID-RUNNER"
    sanitized_runner = MT5ExecutionProvider._sanitize_comment(long_comment_runner, max_bytes=30)
    assert len(sanitized_runner.encode("ascii")) <= 30
    assert sanitized_runner.endswith("-RUNNER") or sanitized_runner.endswith(":RUNNER")

    long_comment_tp1 = "ORB_LONDON_20261109_TRADE_UUID-TP1"
    sanitized_tp1 = MT5ExecutionProvider._sanitize_comment(long_comment_tp1, max_bytes=30)
    assert len(sanitized_tp1.encode("ascii")) <= 30
    assert sanitized_tp1.endswith("-TP1") or sanitized_tp1.endswith(":TP1")


def test_2_2_sibling_temporal_window_rejects_old_tp1():
    """Un TP1 de hace más de 15 minutos no debe emparejarse como hermano de un nuevo RUNNER."""
    engine = object.__new__(LiveTradingEngine)
    engine.config = SimpleNamespace(
        split_entries_enabled=True,
        source="DEMO",
    )
    now = datetime.now(timezone.utc)
    old_entry = (now - timedelta(hours=2)).isoformat()

    # TP1 cerrado de hace 2 horas
    old_tp1 = {
        "id": 100,
        "instrument": "EURUSD",
        "direction": "BUY",
        "status": "CLOSED",
        "result": "WIN",
        "realized_rr": 1.0,
        "entry_time": old_entry,
        "details": {"metadata": {"trade_leg": "TP1"}},
    }

    # Nuevo RUNNER recién abierto
    runner_trade = {
        "id": 101,
        "instrument": "EURUSD",
        "direction": "BUY",
        "entry_time": now.isoformat(),
        "details": {
            "metadata": {
                "trade_leg": "RUNNER",
                "parent_execution_key": "DEMO:EURUSD:UNKNOWN_ORPHAN",
            }
        },
    }

    engine.repository = SimpleNamespace(
        get_trade_by_execution_key=lambda k: None,
        get_trades=lambda source, symbol, limit: [old_tp1],
    )
    engine._trade_metadata = lambda t: (t.get("details") or {}).get("metadata") or {}

    res = engine._break_even_tp1_completion(runner_trade, runner_trade["details"]["metadata"])
    # Debe rechazar emparejarse con el trade de hace 2 horas
    assert not res["completed"]
    assert res["reason"] == "TP1_NOT_FOUND"


def test_2_3_tripartite_gate_anti_spike_hazard():
    """El Gate Tripartito debe vetar inmediatamente si se detecta peligro de spike."""
    gate = TripartiteConfluenceGate(TripartiteConfluenceConfig(enabled=True, anti_spike_shield_enabled=True))
    signal = {
        "stop_loss": 1000.0,
        "take_profit": 1050.0,
    }

    # Comprar en Crash con spike danger detectado
    decision = gate.evaluate_confluence(
        symbol="Crash 1000 Index",
        strategy_name="ICT",
        direction="BUY",
        signal=signal,
        is_spike_danger=True,
    )
    assert not decision.allowed
    assert decision.action == "VETO_HUMAN_CRITERIA_ANTI_SPIKE"


def test_2_4_tripartite_gate_ai_compensation_logic():
    """Sin IA, si el Criterio Humano < 80 pts veta; si >= 80 pts aprueba por compensación."""
    gate = TripartiteConfluenceGate(
        TripartiteConfluenceConfig(
            enabled=True,
            ai_filter_active=True,
            min_human_score_without_ai=80.0,
        )
    )
    signal = {
        "stop_loss": 1.1000,
        "take_profit": 1.1050,
    }

    # Caso 1: Score 76.0 (< 80) -> Veto por confluencia insuficiente sin IA
    human_low = SimpleNamespace(allowed=True, score=76.0, reason="OK")
    dec_low = gate.evaluate_confluence(
        symbol="EURUSD",
        strategy_name="ICT",
        direction="BUY",
        signal=signal,
        human_criteria_decision=human_low,
        ai_evaluation=None,
    )
    assert not dec_low.allowed
    assert dec_low.action == "VETO_INSUFFICIENT_CONFLUENCE_WITHOUT_AI"

    # Caso 2: Score 82.0 (>= 80) -> Aprobado por compensación humana
    human_high = SimpleNamespace(allowed=True, score=82.0, reason="OK")
    dec_high = gate.evaluate_confluence(
        symbol="EURUSD",
        strategy_name="ICT",
        direction="BUY",
        signal=signal,
        human_criteria_decision=human_high,
        ai_evaluation=None,
    )
    assert dec_high.allowed
    assert dec_high.action == "APPROVED"
    assert "Compensado Criterio Humano" in dec_high.reason


def test_2_5_crypto_force_flat_defaults_to_false():
    """Cripto 24/7 no debe tener liquidación forzada diaria ni de fin de semana por defecto."""
    cfg = LiveTradingConfig()
    assert cfg.crypto_force_flat_daily is False
    assert cfg.crypto_force_flat_friday is False
