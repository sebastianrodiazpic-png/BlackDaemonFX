"""Causal audit indicators; never used to change entry gates."""
import numpy as np
import pandas as pd


def wilder(series, period=14):
    """Wilder smoothing seeded by the first full arithmetic mean."""
    values = pd.to_numeric(series, errors='coerce').to_numpy(dtype=float)
    out = np.full(len(values), np.nan)
    seed = []
    previous = None
    for i, value in enumerate(values):
        if not np.isfinite(value):
            seed, previous = [], None
            continue
        if previous is None:
            seed.append(value)
            if len(seed) == period:
                previous = float(np.mean(seed))
        else:
            previous = (previous * (period - 1) + value) / period
        if previous is not None:
            out[i] = previous
    return pd.Series(out, index=series.index)


def audit_indicators(data, period=14):
    """ATR/ADX(14), past and current candle only; warmup remains missing."""
    result = data.copy()
    high, low, close = (pd.to_numeric(result[k], errors='coerce') for k in ('high','low','close'))
    previous = close.shift(1)
    tr = pd.concat([high-low, (high-previous).abs(), (low-previous).abs()], axis=1).max(axis=1)
    up, down = high.diff(), -low.diff()
    plus = up.where((up > down) & (up > 0), 0.)
    minus = down.where((down > up) & (down > 0), 0.)
    plus.iloc[0:1] = np.nan
    minus.iloc[0:1] = np.nan
    atr = wilder(tr, period)
    p, m = wilder(plus, period), wilder(minus, period)
    total = p + m
    dx = (100 * (p-m).abs() / total.where(total != 0)).where(total != 0, 0.)
    result['atr'] = atr
    result['adx'] = wilder(dx, period)
    return result
