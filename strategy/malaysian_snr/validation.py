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


def av_levels(frame: pd.DataFrame) -> list[dict]:
    """Classic A/V body junctions; wick extremes remain invalidation bounds."""
    levels = []
    opens, highs, lows, closes = (frame[key].to_numpy(dtype=float) for key in ("open", "high", "low", "close"))
    times = frame.time.tolist()
    for i in range(1, len(frame) - 1):
        resistance = closes[i-1] > opens[i-1] and closes[i] < opens[i] and closes[i] <= opens[i-1]
        support = closes[i-1] < opens[i-1] and closes[i] > opens[i] and closes[i] >= opens[i-1]
        if resistance or support:
            levels.append({"type": "A_RESISTANCE" if resistance else "V_SUPPORT",
                           "level": float(closes[i-1]), "break_level": float(closes[i-1]),
                           "wick_bound": float(max(highs[i-1], highs[i]) if resistance else min(lows[i-1], lows[i])),
                           "time": times[i], "idx": i})
    return levels


def level_is_fresh(frame: pd.DataFrame, level: dict) -> bool:
    intermediate = frame.iloc[level["idx"] + 1:-1]
    return not ((intermediate.low <= level["level"]) & (intermediate.high >= level["level"])).any()


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
    if frame.empty or atr <= 0:
        return False
    lows = frame["low"].to_numpy(dtype=float)
    highs = frame["high"].to_numpy(dtype=float)
    opens = frame["open"].to_numpy(dtype=float)
    closes = frame["close"].to_numpy(dtype=float)

    sign = 1 if direction == "BUY" else -1
    last_close = closes[-1]
    last_open = opens[-1]
    distance = sign * (last_close - level)

    if not (0 <= distance <= max_distance_atr * atr and sign * (last_close - last_open) > 0):
        return False

    if direction == "BUY":
        swept = np.any(lows <= level + 0.10 * atr)
        rejected = last_close >= level - 0.05 * atr
        return bool(swept and rejected)
    else:
        swept = np.any(highs >= level - 0.10 * atr)
        rejected = last_close <= level + 0.05 * atr
        return bool(swept and rejected)


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
