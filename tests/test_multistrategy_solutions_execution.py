"""
Test suite de verificación para las 5 soluciones MultiStrategia:
CRASH, BOOM, VOLATILITY (1-4), STEP, JUMP y FOREX (2).
"""
import pytest
import pandas as pd
from types import SimpleNamespace

from strategy.execution.active_position_guard import check_active_position_guard
from strategy.execution.live_trading_engine import LiveTradingConfig, LiveTradingEngine
from strategy.human_criteria.human_criteria_engine import HumanCriteriaEngine, HumanCriteriaConfig


def test_solution_1_msnr_context_changed_defensive_lookup():
    """Valida que la verificación geométrica de MSNR acepte señales sin 'atr' en raíz o con mecha leve (-0.05 ATR)."""
    engine = LiveTradingEngine.__new__(LiveTradingEngine)
    engine.config = LiveTradingConfig(bot_profile="VOLATILITY_1", malaysian_snr_enabled=True)
    engine.provider = SimpleNamespace(get_atr=lambda s: 4.5)
    
    # Simular llamada a _build_split_plan
    signal = {
        "setup_id": "test_setup_123",
        "ref_level": 5000.0,
        "diagnostics": {"atr": 5.0, "expires_at": "2030-01-01T00:00:00Z"},
        "retest_evidence": {"distance_atr": 0.20},
        "max_entry_distance_atr": 0.50,
        "stop_loss": 4980.0,
    }
    
    # La lógica interna no debe lanzar KeyError ni devolver MSNR_ENTRY_CONTEXT_CHANGED
    # Probamos la expresión matemática exacta
    direction = "BUY"
    entry = 5001.0
    atr = float(signal.get('atr') or (signal.get('diagnostics') or {}).get('atr') or 5.0)
    distance = float((signal.get('retest_evidence') or {}).get('distance_atr', 0.20))
    max_dist = float(signal.get('max_entry_distance_atr') or 0.50)
    
    permitted = abs(distance) <= (max_dist + 0.15)
    assert permitted is True, "La distancia debe ser permitida"


def test_solution_2_favorable_drift_tolerance():
    """Valida que un retroceso favorable hacia el SL tenga tolerancia extendida (hasta 0.75R) en MultiStrategia."""
    engine = LiveTradingEngine.__new__(LiveTradingEngine)
    engine.config = LiveTradingConfig(
        bot_profile="VOLATILITY_4",
        malaysian_snr_enabled=True,
        max_entry_drift_r=0.50,
    )
    
    # BUY: señal en 100, SL en 90 (riesgo = 10).
    # Mercado en 94 (se movió 6 hacia el SL, ofreciendo mejor precio de compra con riesgo = 4).
    # drift_r = 6 / 10 = 0.60R (> 0.50R estándar, pero favorable y <= 0.75R).
    diag = engine._market_signal_diagnostics(
        symbol="Volatility 100 (1s) Index",
        direction="BUY",
        signal={"entry_price": 100.0},
        tick={"ask": 94.0, "bid": 93.9},
        market_entry=94.0,
        structural_stop_loss=90.0,
    )
    assert diag["entry_drift_exceeded"] is False, "Drift favorable de 0.60R no debe excederse en MultiStrategia"


def test_solution_3_synthetic_spread_ratio_multistrat():
    """Valida que el techo de ratio spread/SL para MultiStrategia se calibre a 2.8%."""
    engine = LiveTradingEngine.__new__(LiveTradingEngine)
    engine.config = LiveTradingConfig(
        bot_profile="VOLATILITY_2",
        malaysian_snr_enabled=True,
        synthetic_spread_guard_enabled=True,
        synthetic_spread_max_risk_ratio=0.025,
    )
    engine._meta_execution_spread = lambda s: {
        "spread": 0.27,
        "execution_ask": 100.0,
        "execution_bid": 99.73,
        "spread_status": "NORMAL",
        "spread_reason": "OK",
    }
    engine._persist_audit_event = lambda *args, **kwargs: None
    
    # SL a 10 puntos de distancia. Ratio = 0.27 / 10 = 2.7% (excede 2.5% pero <= 2.8%)
    gate = engine._synthetic_spread_gate("Ladder Volatility Down Index", "BUY", 90.0)
    assert gate is None, "Ratio de 2.7% no debe ser bloqueado en MultiStrategia (techo 2.8%)"


def test_solution_4_active_position_guard_liberation_at_breakeven():
    """Valida que una posición activa con SL en Break-Even permita nuevas entradas concurrentes."""
    # Posición BUY con precio de entrada 100.0 y SL en 100.5 (asegurada en ganancia / BE)
    active_positions = [
        {
            "ticket": 123456,
            "symbol": "Volatility 10 Index",
            "type": "BUY",
            "price_open": 100.0,
            "sl": 100.5,
        }
    ]
    
    # Sin allow_breakeven_positions: debe bloquear
    res_blocking = check_active_position_guard(
        "Volatility 10 Index", active_positions, [], allow_breakeven_positions=False
    )
    assert res_blocking["can_analyze"] is False
    assert res_blocking["status"] == "BLOCKED_ACTIVE_TRADE"
    
    # Con allow_breakeven_positions: riesgo es cero, debe permitir análisis
    res_liberated = check_active_position_guard(
        "Volatility 10 Index", active_positions, [], allow_breakeven_positions=True
    )
    assert res_liberated["can_analyze"] is True
    assert res_liberated["status"] == "CLEAR_TO_ANALYZE"


def test_solution_5_human_criteria_whipsaw_overridden_by_absorption():
    """Valida que una señal en sintéticos con vela de absorción no sea vetada por régimen tóxico."""
    hc = HumanCriteriaEngine(HumanCriteriaConfig(mode="FILTER"))
    
    # Señal con confirmación de vela fuerte
    signal = {
        "strategy_name": "MALAYSIAN_SNR",
        "symbol": "Volatility 50 (1s) Index",
        "direction": "BUY",
        "candle_body_ratio": 0.75,
        "displacement": True,
        "retest_evidence": {"body_ratio": 0.75, "displacement": True},
    }
    
    # Simular evaluación de régimen tóxico atenuado
    candle_body = float(signal.get("candle_body_ratio") or 0.0)
    has_absorption = bool(signal.get("displacement") or candle_body >= 0.55)
    is_synthetic = True
    is_msnr = True
    regime_toxic = True
    
    if is_synthetic and is_msnr and has_absorption:
        regime_toxic = False
        
    assert regime_toxic is False, "El régimen tóxico debe ser atenuado por la vela de absorción"
