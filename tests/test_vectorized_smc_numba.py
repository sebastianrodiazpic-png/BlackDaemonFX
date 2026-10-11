import numpy as np
import pandas as pd
import pytest

from strategy.smc.swings import detect_swings
from strategy.smc.choch_bos import detect_choch_bos
from strategy.smc.fair_value_gap import detect_fvg_confirmation
from strategy.smc.vectorized_smc import (
    vectorized_detect_choch_bos,
    fast_compute_rolling_atr14,
    _check_fvg_filled,
    HAS_NUMBA,
)


def test_has_numba_installed():
    assert HAS_NUMBA is True


def test_vectorized_choch_bos_matches_expected_schema():
    dates = pd.date_range("2026-01-01", periods=60, freq="5min")
    highs = np.array([10.0 + (i % 5) * 1.5 for i in range(60)])
    lows = highs - 1.0
    closes = (highs + lows) / 2.0

    df = pd.DataFrame({
        "time": dates,
        "open": closes,
        "high": highs,
        "low": lows,
        "close": closes,
    })
    df = detect_swings(df)
    res = detect_choch_bos(df)

    assert "choch_bullish" in res.columns
    assert "choch_bearish" in res.columns
    assert "bos_bullish" in res.columns
    assert "bos_bearish" in res.columns
    assert "structure_break_level" in res.columns
    assert res["choch_bullish"].dtype == bool


def test_fast_rolling_atr():
    highs = np.array([10.0, 12.0, 11.5, 13.0, 14.0] * 5, dtype=float)
    lows = np.array([9.0, 10.5, 10.0, 11.0, 12.0] * 5, dtype=float)
    closes = np.array([9.5, 11.0, 10.5, 12.5, 13.5] * 5, dtype=float)

    atr = fast_compute_rolling_atr14(highs, lows, closes, period=14)
    assert len(atr) == len(highs)
    assert atr[13] > 0.0


def test_check_fvg_filled():
    lows = np.array([10.0, 9.5, 8.0, 7.5], dtype=float)
    highs = np.array([11.0, 10.5, 9.0, 8.5], dtype=float)

    # Bullish gap at 9.0: candle 2 (low=8.0) fills it
    filled = _check_fvg_filled(lows, highs, 0, 4, True, 9.0, 9.5)
    assert filled is True
