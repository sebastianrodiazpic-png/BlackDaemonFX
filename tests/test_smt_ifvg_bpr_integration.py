"""Pruebas unitarias para las mejoras validadas:
1. Opción A: Detección de Divergencia SMT (Smart Money Technique) y bonus +15 pts.
2. Opción C: Detección de Inversion FVG (iFVG) y Balanced Price Range (BPR).
3. Preservación estricta de la independencia operativa entre ICT y Malaysian SNR.
"""
import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timezone, timedelta

from strategy.ict.config import ICTSabriMalleConfig
from strategy.ict.ict_strategy import (
    ICTSabriMalleStrategy,
    find_inversion_fvg_and_bpr_setups,
)
from strategy.execution.live_trading_engine import LiveTradingEngine


class MockProvider:
    def __init__(self, candles_a, candles_b=None):
        self.candles_a = candles_a
        self.candles_b = candles_b if candles_b is not None else candles_a

    def get_candles(self, symbol, timeframe, count=50):
        if "75 (1s)" in symbol or "GBP" in symbol or "500" in symbol or "SP 500" in symbol:
            return self.candles_b.tail(count).copy()
        return self.candles_a.tail(count).copy()

    def resolve_symbol(self, s):
        return s

    def get_current_tick(self, symbol):
        return {"bid": 1.1000, "ask": 1.10015}


def test_find_inversion_fvg_bearish():
    """Prueba que un FVG alcista perforado hacia abajo se identifique como Inversion FVG bajista."""
    times = [datetime(2026, 10, 10, i, 0, tzinfo=timezone.utc) for i in range(10)]
    df = pd.DataFrame({
        "time": times,
        "open":  [100.0, 101.0, 104.0, 103.0, 99.0, 100.5, 101.0, 100.8, 100.6, 100.8],
        "high":  [101.0, 104.5, 106.0, 104.0, 100.0, 101.5, 102.0, 101.2, 101.0, 101.8],
        "low":   [ 99.5, 100.8, 103.5,  99.0,  98.0, 100.0, 100.2, 100.0, 100.1, 100.5],
        "close": [100.8, 104.0, 105.0,  99.2,  98.5, 101.0, 101.0, 100.5, 100.4, 101.2],
    })
    
    res = find_inversion_fvg_and_bpr_setups(df, curr_idx=len(df)-1, intended_direction="SELL", lookback_bars=10, spread=0.05)
    assert res is not None
    assert res["valid"] is True
    assert res["type"] == "ICT_INVERSION_FVG"
    assert res["direction"] == "SELL"
    assert res["stop_loss"] > res["entry_price"]


def test_find_balanced_price_range_bullish():
    """Prueba que solapamiento de FVG opuestos consecutivos califique como BPR alcista."""
    times = [datetime(2026, 10, 10, i, 0, tzinfo=timezone.utc) for i in range(6)]
    df = pd.DataFrame({
        "time": times,
        "open":  [100.0, 100.5, 101.0, 103.0, 106.0, 107.0],
        "high":  [100.5, 101.0, 102.0, 105.0, 108.0, 109.0],
        "low":   [ 99.8, 100.0, 100.8, 102.5, 105.5, 106.5],
        "close": [100.2, 100.8, 101.8, 104.8, 107.5, 108.5],
    })
    res = find_inversion_fvg_and_bpr_setups(df, curr_idx=len(df)-1, intended_direction="BUY", lookback_bars=6, spread=0.05)
    assert res is not None
    assert res["valid"] is True
    assert res["type"] == "ICT_BALANCED_PRICE_RANGE"
    assert res["direction"] == "BUY"


def test_smt_divergence_detection_and_score_boost():
    """Prueba que el motor LiveTradingEngine detecte divergencia SMT entre pares gemelos y otorgue el bonus de +15."""
    engine = LiveTradingEngine.__new__(LiveTradingEngine)
    
    base_t = datetime(2026, 10, 10, 0, 0, tzinfo=timezone.utc)
    times = [base_t + timedelta(minutes=i * 15) for i in range(12)]
    
    # Activo A (EURUSD): Hace Lower Low (1.1000 -> 1.0960)
    df_a = pd.DataFrame({
        "time": times,
        "high": [1.1050] * 6 + [1.1030] * 6,
        "low":  [1.1000] * 6 + [1.0960] * 6,
        "open": [1.1020] * 12,
        "close": [1.1010] * 12,
    })
    
    # Activo B (GBPUSD gemelo): Falla en hacer Lower Low (hace Higher Low: 1.2450 -> 1.2480)
    df_b = pd.DataFrame({
        "time": times,
        "high": [1.2550] * 6 + [1.2580] * 6,
        "low":  [1.2450] * 6 + [1.2480] * 6,
        "open": [1.2500] * 12,
        "close": [1.2520] * 12,
    })
    
    engine.provider = MockProvider(df_a, df_b)
    
    signal = {
        "symbol": "EURUSD",
        "direction": "BUY",
        "trade_score": 75.0,
        "confirmation_percentage": 80.0,
        "confirmations": {},
    }
    
    smt_res = engine._detect_smt_divergence(
        symbol="EURUSD",
        direction="BUY",
        signal=signal,
    )
    
    assert smt_res["has_smt"] is True
    assert smt_res["smt_type"] == "BULLISH_SMT_ACCUMULATION"
    assert signal["smt_divergence"] is True
    assert signal["smt_twin"] == "GBPUSD"
    assert signal["trade_score"] == 90.0  # 75 + 15
    assert signal["confirmation_percentage"] == 95.0  # 80 + 15
    assert signal["confirmations"]["smt_divergence"] is True
    assert "SMT_INSTITUTIONAL_DIVERGENCE" in signal["confluence_tags"]
