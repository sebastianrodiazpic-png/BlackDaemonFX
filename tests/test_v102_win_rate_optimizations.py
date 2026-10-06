"""Pruebas unitarias para las 3 optimizaciones de Win Rate:
1. Aislamiento técnico de Step Index (M15 y ADX > 25).
2. Umbrales de probabilidad adaptativos por familia en Meta-Etiquetado IA.
3. Filtro de desplazamiento mínimo en Fair Value Gap (FVG >= 1.5x ATR_14).
"""
import pandas as pd
import pytest

from strategy.execution.live_trading_engine import LiveTradingEngine, LiveTradingConfig
from strategy.ai.meta_labeling import MetaLabelingEngine, MetaLabelingConfig
from strategy.smc.fair_value_gap import detect_fvg_confirmation, FVGConfig


# --------------------------------------------------------------------------
# 1. AISLAMIENTO TÉCNICO DE STEP INDEX (M15 Y ADX > 25)
# --------------------------------------------------------------------------
def test_step_blocks_m5_and_m1_confirmation():
    engine = object.__new__(LiveTradingEngine)
    engine.config = LiveTradingConfig(bot_profile="STEP", step_min_adx=25.0)

    # Señal con M5 debe ser rechazada
    signal_m5 = {"adx": 30.0, "confirmation_timeframe": "M5"}
    gate_m5 = engine._step_quality_gate("Step Index 500", signal_m5)
    assert gate_m5 is not None
    assert gate_m5["action"] == "STEP_TIMEFRAME_TOO_LOW"
    assert gate_m5["reason"] == "STEP_REQUIRES_M15_CONFIRMATION"

    # Señal con M1 debe ser rechazada
    signal_m1 = {"adx": 30.0, "timeframe": "M1"}
    gate_m1 = engine._step_quality_gate("Step Index 500", signal_m1)
    assert gate_m1 is not None
    assert gate_m1["action"] == "STEP_TIMEFRAME_TOO_LOW"


def test_step_blocks_adx_below_or_equal_25():
    engine = object.__new__(LiveTradingEngine)
    engine.config = LiveTradingConfig(bot_profile="STEP", step_min_adx=25.0)

    signal_low_adx = {"adx": 24.9, "confirmation_timeframe": "M15"}
    gate = engine._step_quality_gate("Step Index 500", signal_low_adx)
    assert gate is not None
    assert gate["action"] == "STEP_ADX_LOW"
    assert gate["reason"] == "STEP_REQUIRES_M15_ADX_ABOVE_25"

    signal_exact_25 = {"adx": 25.0, "confirmation_timeframe": "M15"}
    gate2 = engine._step_quality_gate("Step Index 500", signal_exact_25)
    assert gate2 is not None
    assert gate2["action"] == "STEP_ADX_LOW"


def test_step_allows_m15_with_high_adx():
    engine = object.__new__(LiveTradingEngine)
    engine.config = LiveTradingConfig(bot_profile="STEP", step_min_adx=25.0)

    signal_valid = {"adx": 28.5, "confirmation_timeframe": "M15"}
    gate = engine._step_quality_gate("Step Index 500", signal_valid)
    assert gate is None


# --------------------------------------------------------------------------
# 2. UMBRALES DE PROBABILIDAD ADAPTATIVOS POR FAMILIA
# --------------------------------------------------------------------------
def test_adaptive_thresholds_resolution():
    engine = MetaLabelingEngine(
        MetaLabelingConfig(
            min_probability=0.55,
            min_probability_forex=0.60,
            min_probability_gold=0.60,
            min_probability_volatility=0.52,
        ),
        worker="GLOBAL",
    )

    # Forex -> 0.60
    assert engine.resolve_min_probability("EURUSD") == 0.60
    assert engine.resolve_min_probability("GBPJPY") == 0.60

    # Gold -> 0.60
    assert engine.resolve_min_probability("XAUUSD") == 0.60
    assert engine.resolve_min_probability("XAUUSDmicro") == 0.60

    # Volatility -> 0.52
    assert engine.resolve_min_probability("Volatility 75 Index") == 0.52
    assert engine.resolve_min_probability("Volatility 25 (1s) Index") == 0.52

    # Boom / Crash / Step -> 0.55
    assert engine.resolve_min_probability("Boom 1000 Index") == 0.55
    assert engine.resolve_min_probability("Crash 500 Index") == 0.55
    assert engine.resolve_min_probability("Step Index") == 0.55


def test_adaptive_threshold_by_worker_name():
    engine_forex = MetaLabelingEngine(
        MetaLabelingConfig(
            min_probability=0.55,
            min_probability_forex=0.60,
            min_probability_gold=0.60,
            min_probability_volatility=0.52,
        ),
        worker="FOREX_2",
    )
    assert engine_forex.resolve_min_probability("EURCHF") == 0.60

    engine_gold = MetaLabelingEngine(
        MetaLabelingConfig(
            min_probability=0.55,
            min_probability_forex=0.60,
            min_probability_gold=0.60,
            min_probability_volatility=0.52,
        ),
        worker="GOLD",
    )
    assert engine_gold.resolve_min_probability("GOLD_SPOT") == 0.60

    engine_vol = MetaLabelingEngine(
        MetaLabelingConfig(
            min_probability=0.55,
            min_probability_forex=0.60,
            min_probability_gold=0.60,
            min_probability_volatility=0.52,
        ),
        worker="VOLATILITY_3",
    )
    assert engine_vol.resolve_min_probability("ANY_VOL") == 0.52


# --------------------------------------------------------------------------
# 3. FILTRO DE DESPLAZAMIENTO MÍNIMO EN FVG (>= 1.5x ATR_14)
# --------------------------------------------------------------------------
def test_fvg_displacement_filter_rejects_low_inertia_gap():
    # 20 velas con ATR estable de 10.0 puntos (high - low = 10.0)
    data = []
    base_price = 1000.0
    for idx in range(20):
        data.append({
            "time": pd.Timestamp("2026-09-30 10:00:00", tz="UTC") + pd.Timedelta(minutes=5 * idx),
            "open": base_price,
            "high": base_price + 6.0,
            "low": base_price - 4.0,  # Range = 10.0
            "close": base_price + 2.0,
        })
        base_price += 2.0
    df = pd.DataFrame(data)

    # Simulamos un gap alcista en las últimas 3 velas (indices 17, 18, 19):
    # Vela 17 (left): high = 1040.0
    # Vela 18 (middle): desplazamiento PEQUEÑO: open = 1041.0, high = 1047.0, low = 1041.0, close = 1046.0 (range = 6.0)
    # ATR_14 es ~10.0 puntos. Un rango de 6.0 es solo 0.6x ATR (muy inferior a 1.5x ATR = 15.0)
    # Vela 19 (current): low = 1043.0, high = 1050.0 (cur_low 1043.0 > left_high 1040.0 -> FVG geométrico de 3.0 pts)
    df.loc[17, "high"] = 1040.0
    df.loc[17, "low"] = 1030.0

    df.loc[18, "open"] = 1041.0
    df.loc[18, "low"] = 1041.0
    df.loc[18, "high"] = 1047.0  # Rango = 6.0 puntos (< 1.5 * 10 = 15.0)
    df.loc[18, "close"] = 1046.0

    df.loc[19, "open"] = 1044.0
    df.loc[19, "low"] = 1043.0  # 1043.0 > 1040.0 (gap existe)
    df.loc[19, "high"] = 1050.0
    df.loc[19, "close"] = 1049.0

    cfg_strict = FVGConfig(enabled=True, min_displacement_atr_multiplier=1.5, lookback=5)
    res = detect_fvg_confirmation(df, "long", confirmation_index=19, config=cfg_strict)
    # Debe ser rechazado por baja inercia
    assert not res["fvg_confirmed"]


def test_fvg_displacement_filter_accepts_strong_institutional_impulse():
    # 20 velas con ATR de ~10.0 puntos
    data = []
    base_price = 1000.0
    for idx in range(20):
        data.append({
            "time": pd.Timestamp("2026-09-30 10:00:00", tz="UTC") + pd.Timedelta(minutes=5 * idx),
            "open": base_price,
            "high": base_price + 6.0,
            "low": base_price - 4.0,  # Range = 10.0
            "close": base_price + 2.0,
        })
        base_price += 2.0
    df = pd.DataFrame(data)

    # Vela 17 (left): high = 1040.0
    df.loc[17, "high"] = 1040.0
    df.loc[17, "low"] = 1030.0

    # Vela 18 (middle): IMPULSO FUERTE institucional: open = 1041.0, high = 1065.0, low = 1041.0 (range = 24.0 pts >= 1.5 * 10)
    df.loc[18, "open"] = 1041.0
    df.loc[18, "low"] = 1041.0
    df.loc[18, "high"] = 1065.0  # Rango = 24.0 puntos (> 1.5 * 10 = 15.0)
    df.loc[18, "close"] = 1064.0

    # Vela 19 (current): low = 1050.0 (cur_low 1050.0 > left_high 1040.0 -> FVG de 10.0 pts)
    df.loc[19, "open"] = 1052.0
    df.loc[19, "low"] = 1050.0
    df.loc[19, "high"] = 1070.0
    df.loc[19, "close"] = 1068.0

    cfg_strict = FVGConfig(enabled=True, min_displacement_atr_multiplier=1.5, lookback=5)
    res = detect_fvg_confirmation(df, "long", confirmation_index=19, config=cfg_strict)
    # Debe ser aceptado con confirmación exitosa y métricas de desplazamiento
    assert res["fvg_confirmed"]
    assert res["fvg_direction"] == "bullish"
    assert res["fvg_displacement_range"] == 24.0
    assert res["fvg_atr_14"] > 0.0
    assert res["fvg_displacement_ratio"] >= 1.5
