"""Causal candle and entry validation shared by the live MSNR analysis."""
from __future__ import annotations

import numpy as np
import pandas as pd


def timeframe_delta(timeframe: str) -> pd.Timedelta:
    unit, amount = timeframe[0].upper(), int(timeframe[1:])
    return pd.Timedelta(**{{"M": "minutes", "H": "hours", "D": "days", "W": "weeks"}[unit]: amount})


def closed_candles(raw: pd.DataFrame, timeframe: str, now: pd.Timestamp) -> pd.DataFrame:
    """`time` is the opening time, as in MT5 and Deriv providers."""
    required = ["time", "open", "high", "low", "close"]
    if raw is None or raw.empty:
        return pd.DataFrame(columns=required)
    if not set(required).issubset(raw.columns):
        raise ValueError("MISSING_OHLC_COLUMNS")
    frame = raw.copy()
    numeric_time = pd.api.types.is_numeric_dtype(frame["time"])
    frame["time"] = pd.to_datetime(frame["time"], utc=True, unit="s" if numeric_time else None, errors="coerce")
    if frame["time"].isna().any():
        raise ValueError("INVALID_CANDLE_TIMES")
    frame = frame[frame["time"] + timeframe_delta(timeframe) <= now]
    if "complete" in frame:
        frame = frame[frame["complete"].fillna(False).astype(bool)]
    frame = frame.sort_values("time").reset_index(drop=True)
    if frame["time"].duplicated().any():
        raise ValueError("DUPLICATE_CANDLE_TIMES")
    for key in required[1:]:
        frame[key] = pd.to_numeric(frame[key], errors="coerce")
    prices = frame[required[1:]].to_numpy(dtype=float)
    if not np.isfinite(prices).all():
        raise ValueError("NON_FINITE_OHLC")
    if ((frame["high"] < frame[["open", "close", "low"]].max(axis=1)) |
            (frame["low"] > frame[["open", "close", "high"]].min(axis=1))).any():
        raise ValueError("INVALID_OHLC_RANGE")
    return frame


def av_levels(frame: pd.DataFrame, include_latest: bool = False, definition: str = 'engulfing') -> list[dict]:
    """Classic A/V body junctions; wick extremes remain invalidation bounds."""
    levels = []
    opens, highs, lows, closes = (frame[key].to_numpy(dtype=float) for key in ("open", "high", "low", "close"))
    times = frame.time.tolist()
    for i in range(1, len(frame) if include_latest else len(frame) - 1):
        resistance = closes[i-1] > opens[i-1] and closes[i] < opens[i]
        support = closes[i-1] < opens[i-1] and closes[i] > opens[i]
        if definition == 'engulfing':
            resistance = resistance and closes[i] <= opens[i-1]
            support = support and closes[i] >= opens[i-1]
        elif definition != 'body_turns':
            raise ValueError('INVALID_AV_DEFINITION')
        if resistance or support:
            levels.append({"type": "A_RESISTANCE" if resistance else "V_SUPPORT",
                           "level": float(closes[i-1]), "break_level": float(closes[i-1]),
                           "wick_bound": float(max(highs[i-1], highs[i]) if resistance else min(lows[i-1], lows[i])),
                           "time": times[i], "idx": i})
    return levels


def level_is_fresh(frame: pd.DataFrame, level: dict) -> bool:
    intermediate = frame.iloc[level["idx"] + 1:-1]
    return not ((intermediate.low <= level["level"]) & (intermediate.high >= level["level"])).any()


def level_freshness(frame: pd.DataFrame, level: dict, atr: float,
                    max_wick_penetration_atr: float = 0.20) -> dict:
    """Count contiguous visits before the breakout; body breaks consume a level."""
    intermediate = frame.iloc[level['idx'] + 1:-1]
    price = float(level['level'])
    resistance = level['type'] == 'A_RESISTANCE'
    touches = ((intermediate.low <= price) & (intermediate.high >= price)).to_numpy()
    visits = int(np.count_nonzero(touches & ~np.r_[False, touches[:-1]])) if len(touches) else 0
    body_break = bool((intermediate.close > price if resistance else intermediate.close < price).any())
    penetration = (intermediate.high - price if resistance else price - intermediate.low)
    depth = max(0., float(penetration.max())) / atr if len(penetration) and atr > 0 else 0.
    consumed = body_break or visits > 1 or depth > max_wick_penetration_atr
    return {'state': 'CONSUMED' if consumed else 'TESTED_ONCE' if visits else 'FRESH',
            'visits': visits, 'body_invalidated': body_break, 'penetration_atr': round(depth, 4)}


def active_av_levels(frame: pd.DataFrame, definition: str = 'engulfing') -> list[dict]:
    """A/V obstacles stay active until a later CLOSED body breaks their role."""
    active = []
    for level in av_levels(frame, include_latest=True, definition=definition):
        later = frame.iloc[level['idx'] + 1:]
        broken = (later.close > level['level'] if level['type'] == 'A_RESISTANCE'
                  else later.close < level['level'])
        if not broken.any():
            active.append(level)
    return active


def retest_confirmation(frame: pd.DataFrame, level: float, direction: str, atr: float,
                        tolerance_atr: float = 0.35, max_distance_atr: float = 0.5,
                        *, allow_sweep: bool = True, allow_zone: bool = True,
                        max_penetration_atr: float = 0.35, recovery_bars: int = 3,
                        min_body_ratio: float = 0.35, require_displacement: bool = False,
                        displacement_atr: float = 0.20, timeframe: str = 'M15',
                        allow_pinbar: bool = False, pinbar_min_wick_ratio: float = .55,
                        pinbar_min_close_ratio: float = .75,
                        allow_direct_touch: bool = False,
                        allow_fakeout_trap: bool = False,
                        max_fakeout_penetration_atr: float = 0.60,
                        fakeout_min_wick_ratio: float = 0.50) -> dict:
    """First bounded visit only, timely recovery, actual sweep or zone rejection.

    Return the FIRST confirming close. Later candles cannot create a fresh
    identity or rescue a consumed visit. Callers use the index to avoid chase.
    """
    waiting = {'confirmed': False, 'reason': 'WAITING_FIRST_RETEST'}
    if (frame.empty or direction not in {'BUY', 'SELL'} or not np.isfinite(atr)
            or atr <= 0 or tolerance_atr < 0 or recovery_bars < 1):
        return waiting
    sign = 1 if direction == 'BUY' else -1
    touches = ((frame.low <= level + tolerance_atr * atr)
               & (frame.high >= level - tolerance_atr * atr)).to_numpy()
    found = np.flatnonzero(touches)
    extremes = frame.low if sign == 1 else frame.high
    # A gap through the level cannot be hidden by a later apparent first touch.
    depths = -sign * (extremes - level) / atr
    hard_limit = max_fakeout_penetration_atr if allow_fakeout_trap else max_penetration_atr
    if not len(found) and (depths > hard_limit).any():
        return {'confirmed': False, 'reason': 'RETEST_PENETRATION_TOO_DEEP'}
    if not len(found):
        return waiting
    first = int(found[0])
    if (depths.iloc[:first] > hard_limit).any():
        return {'confirmed': False, 'reason': 'RETEST_PENETRATION_TOO_DEEP'}

    if allow_direct_touch and len(found):
        last_candle = frame.iloc[-1]
        last_dist = sign * (float(last_candle.close) - level) / atr
        recent_touched = (touches[-1] or (len(touches) >= 2 and touches[-2]) or (len(touches) >= 3 and touches[-3]))
        candle_not_breaking = (sign * float(last_candle.close - last_candle.open) >= -0.20 * atr)
        max_depth = float(depths.max()) if len(depths) else 0.
        if recent_touched and -0.15 <= last_dist <= max_distance_atr and candle_not_breaking and max_depth <= max_penetration_atr:
            span = float(last_candle.high - last_candle.low)
            b = abs(float(last_candle.close - last_candle.open))
            return {
                'confirmed': True,
                'reason': 'RETEST_CONFIRMED',
                'trigger': 'DIRECT_TOUCH_RETEST',
                'touch_index': len(frame) - 1,
                'confirmation_index': len(frame) - 1,
                'body_ratio': round(b / span if span > 0 else 0., 4),
                'penetration_atr': round(max_depth, 4),
                'displacement': True,
                'pinbar_only': False,
                'rejection_wick_ratio': 0.0,
                'close_location': 0.5,
                'distance_atr': round(max(0., last_dist), 4),
            }

    swept = False
    previous_touch = True
    deepest = 0.
    reason = 'WAITING_RETEST_RECOVERY'
    for index in range(first, len(frame)):
        candle = frame.iloc[index]
        if index - first >= recovery_bars:
            return {'confirmed': False, 'reason': 'RETEST_RECOVERY_EXPIRED'}
        if 'time' in frame and index > first and candle.time - frame.iloc[index-1].time != timeframe_delta(timeframe):
            return {'confirmed': False, 'reason': 'RETEST_DATA_GAP'}
        if touches[index] and not previous_touch:
            return {'confirmed': False, 'reason': 'RETEST_CONSUMED'}
        previous_touch = bool(touches[index])
        extreme = float(candle.low if sign == 1 else candle.high)
        depth = max(0., -sign * (extreme - level) / atr)
        deepest = max(deepest, depth)
        span = float(candle.high - candle.low)
        body = sign * float(candle.close - candle.open)
        distance = sign * (float(candle.close) - level) / atr
        body_ratio = body / span if span > 0 else 0.
        close_location = (float(candle.close - candle.low) / span if sign == 1
                          else float(candle.high - candle.close) / span) if span > 0 else 0.
        rejection_wick = (float(min(candle.open, candle.close) - candle.low) if sign == 1
                          else float(candle.high - max(candle.open, candle.close)))
        wick_ratio = rejection_wick / span if span > 0 else 0.

        fakeout_trap = False
        if depth > max_penetration_atr:
            if (allow_fakeout_trap and depth <= max_fakeout_penetration_atr
                    and wick_ratio >= fakeout_min_wick_ratio
                    and distance >= -0.10):
                fakeout_trap = True
            else:
                return {'confirmed': False, 'reason': 'RETEST_PENETRATION_TOO_DEEP'}

        swept = swept or bool(touches[index] and sign * (extreme - level) < 0) or fakeout_trap
        strong = (body_ratio >= min_body_ratio and close_location >= .50)
        # Tested-once entries retain their original displacement and body minimum.
        pinbar = (allow_pinbar and touches[index] and swept and body > 0
                  and wick_ratio >= pinbar_min_wick_ratio
                  and close_location >= pinbar_min_close_ratio)
        pinbar_only = pinbar and not strong
        strong = strong or pinbar or fakeout_trap
        if require_displacement:
            strong = strong and body >= displacement_atr * atr and body_ratio >= .50
        reason = ('ENTRY_TOO_FAR_FROM_LEVEL' if distance > max_distance_atr else
                  'RETEST_WEAK_RECOVERY' if 0 <= distance and not strong else 'WAITING_RETEST_RECOVERY')
        trigger = ('SNR_FAKEOUT_TRAP_SWEEP' if fakeout_trap
                   else 'SNR_PINBAR_SWEEP_RECLAIM' if pinbar_only
                   else 'CRT_M15_SWEEP_AND_ABSORPTION_CLOSE' if swept and allow_sweep
                   else 'M15_ZONE_REJECTION_CLOSE' if allow_zone else None)
        if trigger and 0 <= distance <= max_distance_atr and strong:
            return {'confirmed': True, 'reason': 'RETEST_CONFIRMED', 'trigger': trigger,
                    'touch_index': first, 'confirmation_index': index,
                    'body_ratio': round(body_ratio, 4), 'penetration_atr': round(deepest, 4),
                    'displacement': bool(body >= displacement_atr * atr),
                    'pinbar_only': bool(pinbar_only), 'rejection_wick_ratio': round(wick_ratio, 4),
                    'close_location': round(close_location, 4),
                    'distance_atr': round(distance, 4),
                    'fakeout_trap': bool(fakeout_trap)}
    return {'confirmed': False, 'reason': reason}


def confirmed_retest(frame: pd.DataFrame, level: float, direction: str, atr: float,
                     tolerance_atr: float = 0.35, max_distance_atr: float = 0.5,
                     use_crt_trigger: bool = False) -> bool:
    """Require a bounded touch followed by a directional closed M15 recovery."""
    if use_crt_trigger:
        return confirmed_crt_retest(frame, level, direction, atr, tolerance_atr, max_distance_atr)
    if frame.empty or atr <= 0:
        return False
    tolerance = tolerance_atr * atr
    touches = (frame.low <= level + tolerance) & (frame.high >= level - tolerance)
    if not touches.any():
        return False
    last = frame.iloc[-1]
    sign = 1 if direction == "BUY" else -1
    distance = sign * (float(last.close) - level)
    return bool(0 <= distance <= max_distance_atr * atr and sign * (last.close - last.open) > 0)


def confirmed_crt_retest(frame: pd.DataFrame, level: float, direction: str, atr: float,
                         tolerance_atr: float = 0.35, max_distance_atr: float = 0.5) -> bool:
    """Candle Range Theory (CRT) sweep + rejection confirmation.

    Exige:
    1. Barrido de liquidez (Sweep) del nivel por la mecha en M15.
    2. Rechazo y absorción: la vela cierra regresando dentro del nivel y en dirección del bias.
    3. Distancia acotada hacia la entrada (sin sobre-extensión).
    """
    evidence = retest_confirmation(frame, level, direction, atr, tolerance_atr,
                                  max_distance_atr, allow_zone=False)
    return bool(evidence['confirmed'] and evidence['confirmation_index'] == len(frame) - 1)


def quasimodo_candidates(frame: pd.DataFrame, radius: int = 2) -> list[dict]:
    """Confirmed alternating swings, head sweep and a later closing BOS.

    A pivot is available only after `radius` bars to its right have closed.
    The latest closed H1 must be the first closing break following the head.
    """
    swings = []
    highs, lows, closes = (frame[key].to_numpy(dtype=float) for key in ("high", "low", "close"))
    for i in range(radius, len(frame) - radius):
        high = highs[i] > max(highs[i-radius:i].max(), highs[i+1:i+radius+1].max())
        low = lows[i] < min(lows[i-radius:i].min(), lows[i+1:i+radius+1].min())
        if high == low:
            continue
        point = {"type": "HIGH" if high else "LOW", "idx": i,
                 "price": float(highs[i] if high else lows[i])}
        if swings and swings[-1]["type"] == point["type"]:
            if (high and point["price"] > swings[-1]["price"]) or (low and point["price"] < swings[-1]["price"]):
                swings[-1] = point
        else:
            swings.append(point)
    candidates = []
    for a, b, head in zip(swings, swings[1:], swings[2:]):
        bullish = (a["type"] == "LOW" and b["type"] == "HIGH" and head["type"] == "LOW" and head["price"] < a["price"])
        bearish = (a["type"] == "HIGH" and b["type"] == "LOW" and head["type"] == "HIGH" and head["price"] > a["price"])
        if not (bullish or bearish):
            continue
        # Do not retroactively use a pivot before its right-hand confirmation.
        offset = head["idx"] + radius + 1
        after = closes[offset:]
        breaks = np.flatnonzero(after > b["price"] if bullish else after < b["price"])
        if len(breaks) and offset + breaks[0] == len(frame) - 1:
            candidates.append({"direction": "BUY" if bullish else "SELL", "shoulder": a["price"],
                               "head": head["price"], "neckline": b["price"]})
    return list(reversed(candidates))


def quasimodo_continuation_candidates(frame: pd.DataFrame, radius: int = 2) -> list[dict]:
    """Confirmed Quasimodo Continuation (QMC) pattern:
    Bullish QMC (Trend continuation):
      - Swing A: HIGH (Left Shoulder at price S1)
      - Swing B: LOW (Retracement valley)
      - Swing HEAD: HIGH (Head: Higher High, Head > S1)
      - BOS: First closing break of Head in the latest closed candle.
      Retest target is Left Shoulder (S1) acting as Support.
    Bearish QMC (Trend continuation):
      - Swing A: LOW (Left Shoulder at price S1)
      - Swing B: HIGH (Retracement peak)
      - Swing HEAD: LOW (Head: Lower Low, Head < S1)
      - BOS: First closing break of Head downward in the latest closed candle.
      Retest target is Left Shoulder (S1) acting as Resistance.
    """
    swings = []
    highs, lows, closes = (frame[key].to_numpy(dtype=float) for key in ("high", "low", "close"))
    for i in range(radius, len(frame) - radius):
        high = highs[i] > max(highs[i-radius:i].max(), highs[i+1:i+radius+1].max())
        low = lows[i] < min(lows[i-radius:i].min(), lows[i+1:i+radius+1].min())
        if high == low:
            continue
        point = {"type": "HIGH" if high else "LOW", "idx": i,
                 "price": float(highs[i] if high else lows[i])}
        if swings and swings[-1]["type"] == point["type"]:
            if (high and point["price"] > swings[-1]["price"]) or (low and point["price"] < swings[-1]["price"]):
                swings[-1] = point
        else:
            swings.append(point)
    candidates = []
    for a, b, head in zip(swings, swings[1:], swings[2:]):
        bullish = (a["type"] == "HIGH" and b["type"] == "LOW" and
                   head["type"] == "HIGH" and head["price"] > a["price"])
        bearish = (a["type"] == "LOW" and b["type"] == "HIGH" and
                   head["type"] == "LOW" and head["price"] < a["price"])
        if not (bullish or bearish):
            continue
        offset = head["idx"] + radius + 1
        after = closes[offset:]
        breaks = np.flatnonzero(after > head["price"] if bullish else after < head["price"])
        if len(breaks) and offset + breaks[0] == len(frame) - 1:
            candidates.append({
                "direction": "BUY" if bullish else "SELL",
                "shoulder": a["price"],
                "head": head["price"],
                "neckline": b["price"],
                "invalidation_level": b["price"],
            })
    return list(reversed(candidates))

