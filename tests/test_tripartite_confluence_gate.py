"""
tests/test_tripartite_confluence_gate.py
========================================
Suite de pruebas de regresión para el Gatillo de Confluencia Tripartita:
1. Pilar Estratégico (SMC / SL + TP)
2. Pilar Criterio Humano (Anti-Spike, Clímax, ADX, Spread)
3. Pilar Filtro Activo de IA (Meta-Labeling P(Win) >= 0.50, R > 0)
4. Activos Rehabilitados (Crash 1000, Vol 90 1s, HF 50/100, majors FX)
5. Activos en Poda Estricta / Incompatibles (ORB en sintéticos 24/7, AUDNZD)
6. Interruptores de Configuración y Zero Breaking Changes (Bypass transparente)
7. Integración con LiveTradingEngine y LiveTradingConfig
"""

import os
import pytest
from strategy.confluence.tripartite_confluence_gate import (
    TripartiteConfluenceGate,
    TripartiteConfluenceConfig,
    TripartiteDecision,
    REHABILITATED_ASSETS_BY_STRATEGY,
    STRICT_PRUNED_ASSETS_BY_STRATEGY,
)
from strategy.execution.live_trading_engine import LiveTradingConfig, LiveTradingEngine


def test_tripartite_config_defaults_and_env_switches(monkeypatch):
    """Verifica la carga de interruptores por defecto y mediante variables de entorno."""
    # Por defecto todo activado
    cfg = TripartiteConfluenceConfig()
    assert cfg.enabled is True
    assert cfg.ai_filter_active is True
    assert cfg.human_criteria_active is True
    assert cfg.rehabilitated_assets_enabled is True
    assert cfg.min_ai_probability == 0.50
    assert cfg.anti_spike_shield_enabled is True
    assert cfg.max_climax_candle_body_ratio == 0.85
    assert cfg.min_adx_regime == 20.0

    # Sobrescritura por variable de entorno
    monkeypatch.setenv("DAEMONBLACKFX_TRIPARTITE_CONFLUENCE_ENABLED", "0")
    monkeypatch.setenv("DAEMONBLACKFX_TRIPARTITE_MIN_AI_PROB", "0.55")
    cfg2 = TripartiteConfluenceConfig()
    assert cfg2.enabled is False
    assert cfg2.min_ai_probability == 0.55


def test_zero_breaking_changes_bypass():
    """Verifica que si el interruptor maestro está apagado, el trade se aprueba por BYPASS sin romper nada."""
    cfg = TripartiteConfluenceConfig(enabled=False)
    gate = TripartiteConfluenceGate(config=cfg)

    decision = gate.evaluate_confluence(
        symbol="Crash 1000 Index",
        strategy_name="ICT",
        direction="BUY",
        signal={"sl": 100, "tp": 200},
    )
    assert decision.allowed is True
    assert decision.action == "BYPASS"


def test_strict_pruned_assets_veto():
    """Verifica que los activos incompatibles (ej. sintéticos en ORB o cruces con spread destructivo) sean vetados."""
    gate = TripartiteConfluenceGate()

    # Sintético en ORB (24/7 sin subasta NY)
    dec_orb = gate.evaluate_confluence(
        symbol="Crash 300 Index",
        strategy_name="ORB",
        direction="BUY",
        signal={"sl": 100, "tp": 200},
    )
    assert dec_orb.allowed is False
    assert dec_orb.action == "VETO_STRICT_PRUNING"
    assert "Poda Estricta" in dec_orb.reason or "Incompatible" in dec_orb.reason

    # Cruce Forex tóxico por spread en ICT
    dec_fx = gate.evaluate_confluence(
        symbol="AUDCAD",
        strategy_name="ICT",
        direction="SELL",
        signal={"sl": 100, "tp": 200},
    )
    assert dec_fx.allowed is False
    assert dec_fx.action == "VETO_STRICT_PRUNING"


def test_strategy_pillar_accepts_msnr_tp1_price():
    """Valida que el Pilar 1 reconozca 'tp1_price' y 'tp2_price' usados por Malaysian SNR."""
    gate = TripartiteConfluenceGate()
    sig = {
        "strategy_name": "MALAYSIAN_SNR",
        "direction": "BUY",
        "entry_price": 100.0,
        "stop_loss": 98.0,
        "tp1_price": 102.0,
        "tp2_price": 104.0,
    }
    decision = gate.evaluate_confluence(
        symbol="Step Index 200",
        strategy_name="MALAYSIAN_SNR",
        direction="BUY",
        signal=sig,
    )
    assert decision.strategy_pillar_ok is True
    assert decision.action != "VETO_STRATEGY_PILLAR"


def test_strategy_pillar_missing_sl_tp():
    """Verifica que el Pilar 1 rechace señales incompletas sin SL o TP."""
    gate = TripartiteConfluenceGate()
    dec = gate.evaluate_confluence(
        symbol="Crash 300 Index",
        strategy_name="ICT",
        direction="BUY",
        signal={},  # Sin sl ni tp
    )
    assert dec.allowed is False
    assert dec.action == "VETO_STRATEGY_PILLAR"
    assert dec.strategy_pillar_ok is False


def test_human_criteria_pillar_rejections():
    """Verifica los filtros del Pilar 2: Anti-Spike, Clímax y ADX."""
    gate = TripartiteConfluenceGate()

    # 1. Escudo Anti-Spike adverso
    dec_spike = gate.evaluate_confluence(
        symbol="Crash 300 Index",
        strategy_name="ICT",
        direction="BUY",
        signal={"sl": 100, "tp": 200},
        is_spike_danger=True,
    )
    assert dec_spike.allowed is False
    assert dec_spike.action == "VETO_HUMAN_CRITERIA_ANTI_SPIKE"

    # 2. Vela de clímax sobreextendida (> 85%)
    dec_climax = gate.evaluate_confluence(
        symbol="Boom 500 Index",
        strategy_name="ICT",
        direction="BUY",
        signal={"sl": 100, "tp": 200},
        candle_body_ratio=0.92,
    )
    assert dec_climax.allowed is False
    assert dec_climax.action == "VETO_HUMAN_CRITERIA_CLIMAX"

    # 3. ADX insuficiente (< 20)
    dec_adx = gate.evaluate_confluence(
        symbol="Volatility 75 Index",
        strategy_name="MALAYSIAN_SNR",
        direction="SELL",
        signal={"sl": 100, "tp": 200},
        adx_value=14.5,
    )
    assert dec_adx.allowed is False
    assert dec_adx.action == "VETO_HUMAN_CRITERIA_ADX"


def test_ai_filter_pillar_rejections():
    """Verifica los filtros del Pilar 3: Probabilidad P(Win) y Expectativa Neta R."""
    gate = TripartiteConfluenceGate()

    # Probabilidad baja (< 0.50)
    dec_prob = gate.evaluate_confluence(
        symbol="Step Index",
        strategy_name="ICT",
        direction="BUY",
        signal={"sl": 100, "tp": 200},
        ai_evaluation={"probability": 0.42, "net_expectancy_r": 0.10},
    )
    assert dec_prob.allowed is False
    assert dec_prob.action == "VETO_AI_FILTER_PROBABILITY"
    assert dec_prob.ai_filter_pillar_ok is False

    # Expectativa R insuficiente (< 0.02)
    dec_exp = gate.evaluate_confluence(
        symbol="Step Index",
        strategy_name="ICT",
        direction="BUY",
        signal={"sl": 100, "tp": 200},
        ai_evaluation={"probability": 0.55, "net_expectancy_r": -0.05},
    )
    assert dec_exp.allowed is False
    assert dec_exp.action == "VETO_AI_FILTER_EXPECTANCY"


def test_tripartite_approval_and_rehabilitation():
    """Verifica que un activo podado rehabilitado (ej. Crash 1000) sea admitido con confluencia tripartita."""
    gate = TripartiteConfluenceGate()

    dec = gate.evaluate_confluence(
        symbol="Crash 1000 Index",
        strategy_name="ICT",
        direction="BUY",
        signal={"sl": 100, "tp": 200},
        ai_evaluation={"probability": 0.58, "net_expectancy_r": 0.12},
        candle_body_ratio=0.65,
        adx_value=26.0,
        is_spike_danger=False,
    )
    assert dec.allowed is True
    assert dec.action == "APPROVED"
    assert dec.strategy_pillar_ok is True
    assert dec.human_criteria_pillar_ok is True
    assert dec.ai_filter_pillar_ok is True
    assert dec.is_rehabilitated_asset is True
    assert "ACTIVO REHABILITADO" in dec.reason


def test_live_trading_engine_integration():
    """Verifica la integración fluida con LiveTradingConfig y LiveTradingEngine."""
    cfg = LiveTradingConfig()
    assert hasattr(cfg, "tripartite_confluence_enabled")
    assert hasattr(cfg, "tripartite_ai_filter_active")
    assert hasattr(cfg, "tripartite_human_criteria_active")
    assert hasattr(cfg, "tripartite_rehabilitated_enabled")

    assert "Crash 1000 Index" in REHABILITATED_ASSETS_BY_STRATEGY["ICT"]
    assert "USDCHF" in REHABILITATED_ASSETS_BY_STRATEGY["ORB"]
    assert "AUDCAD" in STRICT_PRUNED_ASSETS_BY_STRATEGY["ICT"]


def test_polymorphic_human_criteria_dict_and_ai_compensation():
    """Valida soporte polimórfico para human_criteria_decision como dict (caso real live_trading_engine)."""
    gate = TripartiteConfluenceGate()

    # Caso 1: Score 82.0 (GRADE_A_ELITE) como dict sin IA disponible -> Debe APROBAR por compensación
    hc_dict_approved = {
        "allowed": True,
        "score": 82.0,
        "grade": "GRADE_A_ELITE",
        "reason": "CRITERIO_HUMANO_APROBADO: Score=82.0",
    }
    decision = gate.evaluate_confluence(
        symbol="Volatility 250 (1s) Index",
        strategy_name="MALAYSIAN_SNR",
        direction="BUY",
        signal={"sl": 0.22, "tp1_price": 0.228, "tp2_price": 0.23},
        human_criteria_decision=hc_dict_approved,
        ai_evaluation=None,  # Inferencia IA no disponible
    )
    assert decision.allowed is True
    assert decision.action == "APPROVED"
    assert decision.human_criteria_score == 82.0
    assert "Compensado Criterio Humano" in decision.reason

    # Caso 2: Score 75.0 como dict sin IA disponible -> Debe VETAR (< 80.0)
    hc_dict_below = {
        "allowed": True,
        "score": 75.0,
        "grade": "GRADE_B_ACCEPTABLE",
        "reason": "CRITERIO_HUMANO_APROBADO: Score=75.0",
    }
    decision_veto = gate.evaluate_confluence(
        symbol="Volatility 250 (1s) Index",
        strategy_name="MALAYSIAN_SNR",
        direction="BUY",
        signal={"sl": 0.22, "tp1_price": 0.228, "tp2_price": 0.23},
        human_criteria_decision=hc_dict_below,
        ai_evaluation=None,
    )
    assert decision_veto.allowed is False
    assert decision_veto.action == "VETO_INSUFFICIENT_CONFLUENCE_WITHOUT_AI"
    assert decision_veto.human_criteria_score == 75.0

    # Caso 3: Dict con allowed=False -> Debe VETAR con VETO_HUMAN_CRITERIA
    hc_dict_rejected = {
        "allowed": False,
        "score": 60.0,
        "grade": "GRADE_C_SUBPAR",
        "reason": "CRITERIO_HUMANO_VETO:TOXIC_CHOPPY_REGIME",
    }
    decision_rejected = gate.evaluate_confluence(
        symbol="Jump 100 Index",
        strategy_name="ICT",
        direction="SELL",
        signal={"sl": 71.6, "tp": 65.3},
        human_criteria_decision=hc_dict_rejected,
    )
    assert decision_rejected.allowed is False
    assert decision_rejected.action == "VETO_HUMAN_CRITERIA"
    assert "TOXIC_CHOPPY_REGIME" in decision_rejected.reason
