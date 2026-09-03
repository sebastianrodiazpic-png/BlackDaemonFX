import pandas as pd

from strategy.smc.h1_doji_extremes import H1ExtremeDojiConfig, detect_h1_extreme_doji


def _base_frame(count=30):
    rows=[]
    for i in range(count):
        base=100.0 + (i * 0.1)
        rows.append({
            "time": pd.Timestamp("2026-08-20T00:00:00Z") + pd.Timedelta(hours=i),
            "open": base,
            "high": base + 1.0,
            "low": base - 1.0,
            "close": base + 0.4,
            "zone": "equilibrium",
        })
    return pd.DataFrame(rows)


def test_bullish_h1_doji_at_lower_extreme_is_optional_confirmation():
    df=_base_frame()
    # Construye un rango visible y un Doji de rechazo en el extremo inferior.
    df.loc[:, "high"] = [110 + (i % 3) for i in range(len(df))]
    df.loc[:, "low"] = [100 + (i % 3) for i in range(len(df))]
    df.loc[:, "open"] = 106.0
    df.loc[:, "close"] = 107.0
    i=len(df)-1
    df.loc[i, ["open","close","high","low","zone"]] = [101.10, 101.15, 102.0, 99.8, "discount"]

    result=detect_h1_extreme_doji(df, direction="BUY", config=H1ExtremeDojiConfig(max_age_candles=1))

    assert result["h1_doji_confirmation"] is True
    assert result["h1_doji_direction"] == "BUY"
    assert "ALCISTA" in result["h1_doji_type"]
    assert result["h1_doji_body_ratio"] <= 0.10
    assert result["h1_doji_lower_wick_ratio"] >= 0.35


def test_bearish_h1_doji_at_upper_extreme_is_optional_confirmation():
    df=_base_frame()
    df.loc[:, "high"] = [110 + (i % 3) for i in range(len(df))]
    df.loc[:, "low"] = [100 + (i % 3) for i in range(len(df))]
    df.loc[:, "open"] = 106.0
    df.loc[:, "close"] = 105.0
    i=len(df)-1
    df.loc[i, ["open","close","high","low","zone"]] = [111.00, 110.95, 112.3, 110.6, "premium"]

    result=detect_h1_extreme_doji(df, direction="SELL")

    assert result["h1_doji_confirmation"] is True
    assert result["h1_doji_direction"] == "SELL"
    assert "BAJISTA" in result["h1_doji_type"]
    assert result["h1_doji_upper_wick_ratio"] >= 0.35


def test_doji_in_middle_of_range_does_not_confirm():
    df=_base_frame()
    df.loc[:, "high"] = 110.0
    df.loc[:, "low"] = 100.0
    df.loc[:, "open"] = 106.0
    df.loc[:, "close"] = 106.5
    i=len(df)-1
    df.loc[i, ["open","close","high","low","zone"]] = [105.00, 105.02, 106.0, 104.0, "equilibrium"]

    result=detect_h1_extreme_doji(df, direction="BUY")

    assert result["h1_doji_confirmation"] is False


def test_disabled_doji_never_blocks_or_confirms():
    df=_base_frame()
    result=detect_h1_extreme_doji(df, direction="BUY", config=H1ExtremeDojiConfig(enabled=False))
    assert result["h1_doji_enabled"] is False
    assert result["h1_doji_confirmation"] is False
    assert result["h1_doji_reason"] == "DETECCION_DOJI_H1_DESACTIVADA"
