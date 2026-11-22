"""tests/test_human_criteria_calibrations.py - Validación de las optimizaciones cuantitativas de Criterio Humano.

Cubre:
1. Exención de ADX para activos de salto discreto (Step / Jump Indices) evitando falsos negativos.
2. Detección afinada de vela clímax parabólica (body_ratio >= 0.80).
3. Veto de fricción excesiva por spread / slippage vs Stop Loss (> 12%).
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from strategy.human_criteria.config import HumanCriteriaConfig, MODE_FILTER
from strategy.human_criteria.human_criteria_engine import HumanCriteriaEngine


def _build_candles(n: int, base: float = 100.0, trend: float = 0.5, noise: float = 0.05) -> pd.DataFrame:
    dates = pd.date_range("2026-01-01", periods=n, freq="1h", tz="UTC")
    closes = base + np.arange(n) * trend + np.sin(np.linspace(0, 3.14, n)) * noise
    opens = closes - trend * 0.5
    highs = np.maximum(opens, closes) + 0.3
    lows = np.minimum(opens, closes) - 0.3
    return pd.DataFrame({
        "time": dates,
        "open": opens,
        "high": highs,
        "low": lows,
        "close": closes,
    })


def _build_oscillating_candles(n: int = 60) -> pd.DataFrame:
    closes = np.array([100.0, 101.0] * (n // 2))
    opens = np.array([100.5, 100.5] * (n // 2))
    highs = closes + 0.5
    lows = closes - 0.5
    dates = pd.date_range("2026-01-01", periods=n, freq="1h", tz="UTC")
    return pd.DataFrame({
        "time": dates,
        "open": opens,
        "high": highs,
        "low": lows,
        "close": closes,
    })


def test_step_jump_adx_guard_exempt_allows_step_index(monkeypatch):
    monkeypatch.setenv("DAEMONBLACKFX_HC_STEP_JUMP_ADX_EXEMPT", "1")
    cfg = HumanCriteriaConfig(enabled=True, mode=MODE_FILTER, step_jump_adx_guard_exempt=True)
    engine = HumanCriteriaEngine(cfg)

    df_h1 = _build_oscillating_candles(60)
    df_ltf = df_h1.tail(20).copy()

    signal = {
        "strategy_name": "AMR_SMC",
        "entry_price": 100.5,
        "stop_loss": 98.0,
        "take_profit": 105.0,
        "spread": 0.05,
    }

    # Step Index con exención activada
    dec_step = engine.evaluate_candidate(
        symbol="Step Index 100",
        direction="BUY",
        signal=signal,
        df_h1=df_h1,
        df_ltf=df_ltf,
        current_spread=0.05,
    )
    assert dec_step.details["regime"]["step_jump_exempt"] is True
    assert dec_step.details["regime"]["is_toxic"] is False
    # No debe estar vetado por TOXIC_CHOPPY_REGIME
    assert dec_step.action != "HUMAN_CRITERIA_TOXIC_REGIME_BLOCKED"


def test_step_jump_adx_guard_disabled_blocks_on_toxic_regime():
    cfg = HumanCriteriaConfig(
        enabled=True,
        mode=MODE_FILTER,
        step_jump_adx_guard_exempt=False,
    )
    engine = HumanCriteriaEngine(cfg)

    df_h1 = _build_oscillating_candles(60)
    df_ltf = df_h1.tail(20).copy()

    signal = {
        "strategy_name": "AMR_SMC",
        "entry_price": 100.5,
        "stop_loss": 98.0,
        "take_profit": 105.0,
        "spread": 0.05,
    }

    dec = engine.evaluate_candidate(
        symbol="Step Index 100",
        direction="BUY",
        signal=signal,
        df_h1=df_h1,
        df_ltf=df_ltf,
        current_spread=0.05,
    )
    assert dec.details["regime"]["step_jump_exempt"] is False
    assert dec.details["regime"]["is_toxic"] is True
    assert dec.allowed is False
    assert dec.action == "HUMAN_CRITERIA_TOXIC_REGIME_BLOCKED"


def test_climax_body_ratio_threshold_veto():
    cfg = HumanCriteriaConfig(enabled=True, mode=MODE_FILTER, synthetic_climax_body_ratio=0.80)
    engine = HumanCriteriaEngine(cfg)

    df_h1 = _build_candles(n=60, base=100.0, trend=0.8, noise=0.01)
    df_ltf = _build_candles(n=20, base=145.0, trend=0.2, noise=0.01)

    # Modificar última vela LTF para simular un marubozu parabólico extremo (cuerpo > 85%, sin mechas)
    idx = len(df_ltf) - 1
    df_ltf.loc[idx, "open"] = 145.0
    df_ltf.loc[idx, "close"] = 150.0
    df_ltf.loc[idx, "high"] = 150.2  # mecha sup: 0.2 / 5.4 = 3.7% (< 15%)
    df_ltf.loc[idx, "low"] = 144.8   # cuerpo: 5.0 / 5.4 = 92.5% (> 80%)

    signal = {
        "strategy_name": "ICT",
        "entry_price": 150.0,
        "stop_loss": 146.0,
        "take_profit": 158.0,
        "spread": 0.05,
    }

    dec = engine.evaluate_candidate(
        symbol="Volatility 75 Index",
        direction="BUY",
        signal=signal,
        df_h1=df_h1,
        df_ltf=df_ltf,
        current_spread=0.05,
    )
    assert dec.allowed is False
    assert dec.action == "HUMAN_CRITERIA_CLIMAX_BLOCKED"
    assert "PARABOLIC_CLIMAX_OVEREXTENSION" in dec.reason


def test_spread_friction_veto_exceeding_threshold():
    cfg = HumanCriteriaConfig(
        enabled=True,
        mode=MODE_FILTER,
        max_spread_to_sl_ratio=0.12,
        spread_friction_veto_enabled=True,
    )
    engine = HumanCriteriaEngine(cfg)

    # Tendencia limpia y estable para evitar que choque con otros filtros
    df_h1 = _build_candles(n=60, base=100.0, trend=1.5, noise=0.01)
    df_ltf = _build_candles(n=20, base=180.0, trend=0.5, noise=0.01)

    # Entrada 180, SL 178 (distancia SL = 2.0). Spread = 0.35 (0.35 / 2.0 = 17.5% > 12%)
    signal = {
        "strategy_name": "SMC",
        "entry_price": 180.0,
        "stop_loss": 178.0,
        "take_profit": 186.0,
        "spread": 0.35,
    }

    dec = engine.evaluate_candidate(
        symbol="Volatility 100 Index",
        direction="BUY",
        signal=signal,
        df_h1=df_h1,
        df_ltf=df_ltf,
        current_spread=0.35,
    )
    assert dec.allowed is False
    assert dec.action == "HUMAN_CRITERIA_SPREAD_FRICTION_BLOCKED"
    assert "EXCESSIVE_SPREAD_FRICTION" in dec.reason


def test_spread_friction_allowed_when_within_limit():
    cfg = HumanCriteriaConfig(
        enabled=True,
        mode=MODE_FILTER,
        max_spread_to_sl_ratio=0.12,
        spread_friction_veto_enabled=True,
    )
    engine = HumanCriteriaEngine(cfg)

    df_h1 = _build_candles(n=60, base=100.0, trend=1.5, noise=0.01)
    df_ltf = _build_candles(n=20, base=180.0, trend=0.5, noise=0.01)

    # Entrada 180, SL 178 (distancia SL = 2.0). Spread = 0.08 (0.08 / 2.0 = 4.0% < 12%)
    signal = {
        "strategy_name": "SMC",
        "entry_price": 180.0,
        "stop_loss": 178.0,
        "take_profit": 186.0,
        "spread": 0.08,
    }

    dec = engine.evaluate_candidate(
        symbol="Volatility 100 Index",
        direction="BUY",
        signal=signal,
        df_h1=df_h1,
        df_ltf=df_ltf,
        current_spread=0.08,
    )
    assert dec.details["spread"]["is_excessive"] is False
    assert dec.action != "HUMAN_CRITERIA_SPREAD_FRICTION_BLOCKED"


def test_adverse_seller_wick_vetoed_on_buy():
    """Un intento de compra tras una vela con 50% de mecha superior (vendedores) y 5% inferior es bloqueado."""
    cfg = HumanCriteriaConfig(
        enabled=True,
        mode=MODE_FILTER,
        adverse_wick_veto_enabled=True,
        max_adverse_wick_ratio=0.40,
        min_rejection_wick_ratio=0.20,
    )
    engine = HumanCriteriaEngine(cfg)

    df_h1 = _build_candles(n=60, base=100.0, trend=1.0, noise=0.01)
    df_ltf = _build_candles(n=20, base=150.0, trend=0.2, noise=0.01)

    # Última vela con mecha superior masiva (Range=10, Open=152, Close=154, High=160, Low=151.5)
    # Upper wick = 160 - 154 = 6.0 (60% del rango)
    # Lower wick = 152 - 151.5 = 0.5 (5% del rango)
    df_ltf.iloc[-1, df_ltf.columns.get_loc("open")] = 152.0
    df_ltf.iloc[-1, df_ltf.columns.get_loc("close")] = 154.0
    df_ltf.iloc[-1, df_ltf.columns.get_loc("high")] = 160.0
    df_ltf.iloc[-1, df_ltf.columns.get_loc("low")] = 151.5

    signal = {
        "strategy_name": "SMC",
        "entry_price": 154.0,
        "stop_loss": 149.0,
        "take_profit": 164.0,
        "spread": 0.05,
    }

    dec = engine.evaluate_candidate(
        symbol="Volatility 75 Index",
        direction="BUY",
        signal=signal,
        df_h1=df_h1,
        df_ltf=df_ltf,
        current_spread=0.05,
    )
    assert dec.allowed is False
    assert dec.action == "HUMAN_CRITERIA_ADVERSE_WICK_BLOCKED"
    assert "ADVERSE_SELLER_WICK_REJECTION" in dec.reason


def test_adverse_buyer_wick_vetoed_on_sell():
    """Un intento de venta tras una vela con 50% de mecha inferior (compradores) y 5% superior es bloqueado."""
    cfg = HumanCriteriaConfig(
        enabled=True,
        mode=MODE_FILTER,
        adverse_wick_veto_enabled=True,
        max_adverse_wick_ratio=0.40,
        min_rejection_wick_ratio=0.20,
    )
    engine = HumanCriteriaEngine(cfg)

    # H1 bajista para no vetar por contratendencia
    df_h1 = _build_candles(n=60, base=200.0, trend=-1.0, noise=0.01)
    df_ltf = _build_candles(n=20, base=150.0, trend=-0.2, noise=0.01)

    # Última vela con mecha inferior masiva (Range=10, Open=148, Close=146, High=148.5, Low=140)
    # Lower wick = 146 - 140 = 6.0 (60% del rango)
    # Upper wick = 148.5 - 148 = 0.5 (5% del rango)
    df_ltf.iloc[-1, df_ltf.columns.get_loc("open")] = 148.0
    df_ltf.iloc[-1, df_ltf.columns.get_loc("close")] = 146.0
    df_ltf.iloc[-1, df_ltf.columns.get_loc("high")] = 148.5
    df_ltf.iloc[-1, df_ltf.columns.get_loc("low")] = 140.0

    signal = {
        "strategy_name": "SMC",
        "entry_price": 146.0,
        "stop_loss": 151.0,
        "take_profit": 136.0,
        "spread": 0.05,
    }

    dec = engine.evaluate_candidate(
        symbol="Volatility 75 Index",
        direction="SELL",
        signal=signal,
        df_h1=df_h1,
        df_ltf=df_ltf,
        current_spread=0.05,
    )
    assert dec.allowed is False
    assert dec.action == "HUMAN_CRITERIA_ADVERSE_WICK_BLOCKED"
    assert "ADVERSE_BUYER_WICK_REJECTION" in dec.reason


def test_absorption_favorable_wick_allowed():
    """Una vela con mecha de absorción favorable a la dirección del trade pasa sin veto."""
    cfg = HumanCriteriaConfig(
        enabled=True,
        mode=MODE_FILTER,
        adverse_wick_veto_enabled=True,
        max_adverse_wick_ratio=0.40,
        min_rejection_wick_ratio=0.20,
    )
    engine = HumanCriteriaEngine(cfg)

    df_h1 = _build_candles(n=60, base=100.0, trend=1.0, noise=0.01)
    df_ltf = _build_candles(n=20, base=150.0, trend=0.2, noise=0.01)

    # Compra con mecha inferior de defensa (Lower wick = 152 - 148 = 4.0 / 10 = 40%)
    df_ltf.iloc[-1, df_ltf.columns.get_loc("open")] = 152.0
    df_ltf.iloc[-1, df_ltf.columns.get_loc("close")] = 157.0
    df_ltf.iloc[-1, df_ltf.columns.get_loc("high")] = 158.0
    df_ltf.iloc[-1, df_ltf.columns.get_loc("low")] = 148.0

    signal = {
        "strategy_name": "SMC",
        "entry_price": 157.0,
        "stop_loss": 147.0,
        "take_profit": 167.0,
        "spread": 0.05,
    }

    dec = engine.evaluate_candidate(
        symbol="Volatility 75 Index",
        direction="BUY",
        signal=signal,
        df_h1=df_h1,
        df_ltf=df_ltf,
        current_spread=0.05,
    )
    assert dec.allowed is True
    assert dec.action == "HUMAN_CRITERIA_PASSED"


def test_high_conviction_override_unlocks_jump_signal():
    """Señales sintéticas con ML probabilidad >= 0.85 y confluencia >= 85% se flexibilizan a umbral 70.0."""
    cfg = HumanCriteriaConfig(
        enabled=True,
        mode=MODE_FILTER,
        synthetic_min_score_threshold=75.0,
        high_conviction_override_enabled=True,
        high_conviction_min_score_threshold=70.0,
    )
    engine = HumanCriteriaEngine(cfg)

    # Creamos velas sintéticas alineadas con tendencia bajista en H1
    df_h1 = _build_candles(n=60, base=50.0, trend=-0.05, noise=0.01)
    df_ltf = _build_candles(n=20, base=46.0, trend=-0.05, noise=0.01)

    # Señal idéntica a la detectada en Jump 100 con ML = 1.0 y Score 100
    signal_high_conv = {
        "strategy_name": "ICT",
        "entry_price": 45.53,
        "stop_loss": 46.18,
        "take_profit": 44.23,
        "trade_score": 100.0,
        "confirmation_percentage": 100.0,
        "ict_msnr_confluence": True,
        "meta_label": {
            "probability": 1.0,
            "net_expectancy_r": 1.68,
        },
    }

    dec = engine.evaluate_candidate(
        symbol="Jump 100 Index",
        direction="SELL",
        signal=signal_high_conv,
        df_h1=df_h1,
        df_ltf=df_ltf,
        current_spread=0.05,
    )
    # Al tener alta convicción, el umbral es 70.0 en lugar de 75.0
    assert dec.allowed is True
    assert "SCORE_BELOW_THRESHOLD" not in dec.reason


def test_high_conviction_override_unlocks_indices_signal():
    """Señales en índices bursátiles (US Tech 100, etc.) con ML prob >= 0.85 y expectativa >= 1.0R se flexibilizan a 70.0."""
    cfg = HumanCriteriaConfig(
        enabled=True,
        mode=MODE_FILTER,
        min_score_threshold=75.0,
        high_conviction_override_enabled=True,
        high_conviction_min_score_threshold=70.0,
    )
    engine = HumanCriteriaEngine(cfg)

    df_h1 = _build_candles(n=60, base=20000.0, trend=-10.0, noise=2.0)
    df_ltf = _build_candles(n=20, base=19400.0, trend=-10.0, noise=2.0)

    signal_indices = {
        "strategy_name": "ICT",
        "entry_price": 19400.0,
        "stop_loss": 19440.0,
        "take_profit": 19320.0,
        "trade_score": 95.0,
        "confirmation_percentage": 95.0,
        "ict_msnr_confluence": True,
        "meta_label": {
            "probability": 0.90,
            "net_expectancy_r": 1.45,
        },
    }

    dec = engine.evaluate_candidate(
        symbol="US Tech 100",
        direction="SELL",
        signal=signal_indices,
        df_h1=df_h1,
        df_ltf=df_ltf,
        current_spread=1.2,
    )
    assert dec.allowed is True
    assert "SCORE_BELOW_THRESHOLD" not in dec.reason


