import pandas as pd

import strategy.smc.confirmation_engine as ce


def _frame():
    times = pd.date_range("2026-08-28", periods=8, freq="5min", tz="UTC")
    return pd.DataFrame({
        "time": times,
        "open":  [100, 99, 98, 99, 97, 98, 99, 100],
        "high":  [101,100, 99,100, 98, 99,100, 102],
        "low":   [ 99, 98, 96, 98, 94, 97, 98,  99],
        "close": [100, 99, 98, 99, 97, 98, 99, 101],
        "swing_low":  [False, False, True, False, True, False, False, False],
        "swing_high": [False, True, False, False, False, False, True, False],
    })


def test_bullish_regular_divergence_detected_between_two_swing_lows(monkeypatch):
    data = _frame()
    fake_rsi = pd.Series([50, 48, 30, 40, 38, 45, 50, 55], index=data.index, dtype=float)
    monkeypatch.setattr(ce, "_rsi", lambda close, period=14: fake_rsi)
    result = ce.detect_rsi_divergence(
        data,
        confirmation_index=7,
        direction="long",
        period=14,
        lookback_candles=80,
    )
    assert result["divergence_detected"] is True
    assert result["divergence_type"] == "DIVERGENCIA_ALCISTA_REGULAR"
    assert result["divergence_price_2"] < result["divergence_price_1"]
    assert result["divergence_rsi_2"] > result["divergence_rsi_1"]


def test_divergence_is_optional_confluence_not_a_mandatory_confirmation():
    cfg = ce.M5ConfirmationConfig()
    assert cfg.divergence_enabled is True
    assert cfg.divergence_bonus_points == 5.0
    # No existe require_divergence: deliberadamente no debe bloquear una entrada SMC.
    assert not hasattr(cfg, "require_divergence")
