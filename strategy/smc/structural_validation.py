"""Causal SMC evidence. Inputs contain closed candles only, in time order."""
import numpy as np
import pandas as pd


def fractal_pivots(data, n=5):
    if not isinstance(n, int) or n < 1:
        raise ValueError("Fractal window must be a positive integer")
    high = pd.to_numeric(data.high, errors="coerce")
    low = pd.to_numeric(data.low, errors="coerce")
    valid = np.isfinite(high) & np.isfinite(low) & (high >= low)
    highs, lows = valid.copy(), valid.copy()
    for offset in range(1, n + 1):
        for shift in (offset, -offset):
            highs &= valid.shift(shift, fill_value=False) & (high > high.shift(shift))
            lows &= valid.shift(shift, fill_value=False) & (low < low.shift(shift))
    return highs, lows


def get_h1_structural_range(data, n=5):
    """Latest confirmed high/low; no rolling fallback when evidence is missing."""
    if data is None or len(data) < 2*n+1:
        return None
    highs, lows = fractal_pivots(data, n)
    hi_pos, lo_pos = np.flatnonzero(highs), np.flatnonzero(lows)
    if not len(hi_pos) or not len(lo_pos):
        return None
    hi, lo = float(data.high.iloc[hi_pos[-1]]), float(data.low.iloc[lo_pos[-1]])
    if hi <= lo:
        return None
    return dict(high=hi, low=lo, swing_high=hi, swing_low=lo,
                equilibrium=(hi+lo)/2, method="CONFIRMED_FRACTALS", fractal_window=n,
                high_index=int(hi_pos[-1]), low_index=int(lo_pos[-1]),
                as_of=str(data.time.iloc[-1]) if "time" in data else None)


def validate_m15_ob_structure(data, origin, direction, n=3, impulse_bars=6):
    """Reference must be confirmed by OB close and first crossed after the OB."""
    result = dict(has_structure_break=False, reference_level=None, break_index=None)
    if direction not in {"long", "short"} or not 0 <= origin < len(data):
        return result
    prior = data.iloc[:origin+1]
    highs, lows = fractal_pivots(prior, n)
    positions = np.flatnonzero(highs if direction == "long" else lows)
    if not len(positions):
        return result
    pivot = int(positions[-1])
    level = float(prior.iloc[pivot]["high" if direction == "long" else "low"])
    result["reference_level"] = level
    closes = data.close
    beyond = closes > level if direction == "long" else closes < level
    if beyond.iloc[pivot+n:origin+1].any():
        return result
    for i in range(origin+1, min(len(data), origin+impulse_bars+1)):
        if beyond.iloc[i]:
            result.update(has_structure_break=True, break_index=i)
            break
    return result


def get_h1_structural_range_flexible(data, left=3, right=1, fallback_bars=24):
    """Input is closed H1 candles. Never remove a second, already closed bar."""
    if any(not isinstance(v, int) or v < 1 for v in (left, right, fallback_bars)):
        raise ValueError("Windows must be positive integers")
    if data is None or data.empty or not {"high", "low"}.issubset(data.columns):
        return None
    high = pd.to_numeric(data.high, errors="coerce")
    low = pd.to_numeric(data.low, errors="coerce")
    valid = np.isfinite(high) & np.isfinite(low) & (high >= low)
    highs, lows = valid.copy(), valid.copy()
    for shift in list(range(1, left+1)) + list(range(-right, 0)):
        highs &= valid.shift(shift, fill_value=False) & (high > high.shift(shift))
        lows &= valid.shift(shift, fill_value=False) & (low < low.shift(shift))
    hp, lp = np.flatnonzero(highs), np.flatnonzero(lows)
    hi = float(high.iloc[hp[-1]]) if len(hp) else float("nan")
    lo = float(low.iloc[lp[-1]]) if len(lp) else float("nan")
    fallback = not (np.isfinite(hi) and np.isfinite(lo) and hi > lo)
    if fallback:
        if len(data) < fallback_bars or not valid.iloc[-fallback_bars:].all():
            return None
        hi, lo = float(high.iloc[-fallback_bars:].max()), float(low.iloc[-fallback_bars:].min())
        if hi <= lo:
            return None
    eq = (hi+lo)/2
    return dict(high=hi, low=lo, swing_high=hi, swing_low=lo, equilibrium=eq,
                discount_max=eq, premium_min=eq, left=left, right=right,
                method="CLOSED_ROLLING_FALLBACK" if fallback else "CONFIRMED_ASYMMETRIC_FRACTALS",
                fallback_used=fallback, fallback_bars=fallback_bars,
                high_index=None if fallback else int(hp[-1]),
                low_index=None if fallback else int(lp[-1]),
                as_of=str(data.time.iloc[-1]) if "time" in data else None)


def validate_m15_ob_flexible(data, ob_idx, signal_type="BUY", impulse_bars=8):
    """Use only the supplied closed prefix; report available body/wick evidence."""
    result = dict(has_structure_break=False, break_quality=None, reference_level=None, break_index=None)
    side = str(signal_type).upper()
    if side not in {"BUY", "SELL", "LONG", "SHORT"} or not 0 < ob_idx < len(data):
        return result
    buy = side in {"BUY", "LONG"}
    prior = data.iloc[max(0, ob_idx-15):ob_idx]
    impulse = data.iloc[ob_idx+1:ob_idx+impulse_bars+1]
    if impulse.empty:
        return result
    column = "high" if buy else "low"
    levels = pd.to_numeric(prior[column], errors="coerce")
    if not np.isfinite(levels).all():
        return result
    target = float(levels.max() if buy else levels.min())
    result["reference_level"] = target
    closes = pd.to_numeric(impulse.close, errors="coerce")
    extremes = pd.to_numeric(impulse[column], errors="coerce")
    body = np.isfinite(closes) & (closes > target if buy else closes < target)
    wick = np.isfinite(extremes) & (extremes > target if buy else extremes < target)
    matches = np.flatnonzero(body if body.any() else wick)
    if len(matches):
        result.update(has_structure_break=True, break_quality="BOS" if body.any() else "SWEEP",
                      break_index=ob_idx+1+int(matches[0]))
    return result


def validate_m5_fvg_decoupled(data, choch_index, signal_type="BUY", window=3,
                              confirmation_index=None):
    """All three FVG candles must lie within CHoCH +/- window and the closed prefix."""
    from strategy.smc.fair_value_gap import detect_fvg_confirmation, FVGConfig
    end = len(data)-1 if confirmation_index is None else confirmation_index
    result = detect_fvg_confirmation(data, signal_type, end,
        FVGConfig(lookback=max(1, end-choch_index+window), max_age_candles=max(0, end)),
        choch_indices=[choch_index] if 0 <= choch_index <= end else [], choch_window=window)
    return {**result, "has_fvg": result["fvg_confirmed"],
            "fvg_top": result["fvg_high"], "fvg_bottom": result["fvg_low"]}
