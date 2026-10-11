"""Auditoría y Replay Comparativo Causal de 2 Años:
Malaysian SNR Baseline (Actual) vs Augmented (Storyline D1, CRT M15, Obstáculo 2R).

Evalúa 24 meses completos (Octubre 2024 - Octubre 2026) sobre datos de 19 activos:
Forex (EURUSD, GBPUSD, USDJPY, USDCAD, USDCHF, AUDUSD)
Metales y Commodities (XAUUSD, XAGUSD, US Oil)
Índices (Wall Street 30, US Tech 100, US SP 500)
Cripto (BTCUSD)
Sintéticos (Boom 1000, Crash 1000, Step Index, Vol 75, Vol 100, Jump 50)
"""
from __future__ import annotations

import argparse
import json
import math
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from strategy.malaysian_snr.validation import (
    av_levels,
    level_is_fresh,
    quasimodo_candidates,
    timeframe_delta,
)

from config.symbol_policy import is_direction_allowed
from tools.replay_malaysian_snr_full_universe import ASSET_UNIVERSE

SPREADS = {k: v["base_spread"] for k, v in ASSET_UNIVERSE.items()}
ASSET_CATEGORIES = {k: v["category"] for k, v in ASSET_UNIVERSE.items()}
IS_SYNTH_MAP = {k: v["is_synth"] for k, v in ASSET_UNIVERSE.items()}



def compute_atr(df: pd.DataFrame, period: int = 14) -> pd.Series:
    prev_close = df["close"].shift(1)
    tr = pd.concat([
        df["high"] - df["low"],
        (df["high"] - prev_close).abs(),
        (df["low"] - prev_close).abs(),
    ], axis=1).max(axis=1)
    return tr.rolling(period).mean()


def compute_adx(df: pd.DataFrame, period: int = 14) -> pd.Series:
    high = df["high"]
    low = df["low"]
    close = df["close"]
    prev_close = close.shift(1)
    tr = pd.concat([
        high - low,
        (high - prev_close).abs(),
        (low - prev_close).abs(),
    ], axis=1).max(axis=1)
    up_move = high - high.shift(1)
    down_move = low.shift(1) - low
    plus_dm = np.where((up_move > down_move) & (up_move > 0), up_move, 0.0)
    minus_dm = np.where((down_move > up_move) & (down_move > 0), down_move, 0.0)
    atr = pd.Series(tr).ewm(alpha=1/period, min_periods=period).mean()
    plus_di = 100.0 * pd.Series(plus_dm, index=df.index).ewm(alpha=1/period, min_periods=period).mean() / atr
    minus_di = 100.0 * pd.Series(minus_dm, index=df.index).ewm(alpha=1/period, min_periods=period).mean() / atr
    dx = 100.0 * (plus_di - minus_di).abs() / (plus_di + minus_di).replace(0, 1e-9)
    return dx.ewm(alpha=1/period, min_periods=period).mean()


def load_dataset(symbol: str) -> dict[str, pd.DataFrame] | None:
    prefix = symbol.replace(" ", "_")
    cache_dir = PROJECT_ROOT / "data" / "cache_msnr"
    h1_pkl = cache_dir / f"{prefix}_H1.pkl"
    m15_pkl = cache_dir / f"{prefix}_M15.pkl"

    if h1_pkl.exists() and m15_pkl.exists():
        df_h1 = pd.read_pickle(h1_pkl)
        df_m15 = pd.read_pickle(m15_pkl)
        df_h1["time"] = pd.to_datetime(df_h1["time"], utc=True)
        df_h1 = df_h1.sort_values("time").drop_duplicates("time").reset_index(drop=True)
        df_m15["time"] = pd.to_datetime(df_m15["time"], utc=True)
        df_m15 = df_m15.sort_values("time").drop_duplicates("time").reset_index(drop=True)

        bars_d1 = df_h1.set_index("time").resample("1D", label="left", closed="left")
        df_d1 = bars_d1.agg({"open": "first", "high": "max", "low": "min", "close": "last"}).dropna().reset_index()
        df_d1["time"] = pd.to_datetime(df_d1["time"], utc=True)

        return {"H1": df_h1, "M15": df_m15, "D1": df_d1}

    dirs = [
        PROJECT_ROOT / "data" / "historical",
        PROJECT_ROOT / "data" / "forex_historical",
    ]
    
    h1_path = None
    m15_path = None
    m5_path = None
    
    for d in dirs:
        if (d / f"{prefix}_H1.csv").exists():
            h1_path = d / f"{prefix}_H1.csv"
        if (d / f"{prefix}_M15.csv").exists():
            m15_path = d / f"{prefix}_M15.csv"
        if (d / f"{prefix}_M5.csv").exists():
            m5_path = d / f"{prefix}_M5.csv"

    if h1_path is None:
        return None

    df_h1 = pd.read_csv(h1_path)
    df_h1["time"] = pd.to_datetime(df_h1["time"], utc=True)
    df_h1 = df_h1.sort_values("time").drop_duplicates("time").reset_index(drop=True)

    if m15_path is not None:
        df_m15 = pd.read_csv(m15_path)
        df_m15["time"] = pd.to_datetime(df_m15["time"], utc=True)
        df_m15 = df_m15.sort_values("time").drop_duplicates("time").reset_index(drop=True)
    elif m5_path is not None:
        df_m5 = pd.read_csv(m5_path)
        df_m5["time"] = pd.to_datetime(df_m5["time"], utc=True)
        df_m5 = df_m5.sort_values("time").drop_duplicates("time").reset_index(drop=True)
        bars = df_m5.set_index("time").resample("15min", label="left", closed="left")
        df_m15 = bars.agg({"open": "first", "high": "max", "low": "min", "close": "last"})
        df_m15 = df_m15[bars.close.count() == 3].dropna().reset_index()
    else:
        return None

    bars_d1 = df_h1.set_index("time").resample("1D", label="left", closed="left")
    df_d1 = bars_d1.agg({"open": "first", "high": "max", "low": "min", "close": "last"}).dropna().reset_index()
    df_d1["time"] = pd.to_datetime(df_d1["time"], utc=True)

    return {"H1": df_h1, "M15": df_m15, "D1": df_d1}


def evaluate_crt_m15_rejection_np(
    sub_o: np.ndarray,
    sub_h: np.ndarray,
    sub_l: np.ndarray,
    sub_c: np.ndarray,
    level: float,
    direction: str,
    atr: float,
    tolerance_atr: float = 0.35,
) -> tuple[bool, float, float]:
    if len(sub_c) < 2 or atr <= 0:
        return False, 0.0, 0.0

    tolerance = tolerance_atr * atr
    zone_top = level + tolerance
    zone_bottom = level - tolerance

    if direction == "BUY":
        swept = bool(np.any((sub_l <= zone_top) & (sub_h >= zone_bottom)))
    else:
        swept = bool(np.any((sub_h >= zone_bottom) & (sub_l <= zone_top)))

    if not swept:
        return False, 0.0, 0.0

    c_open = sub_o[-1]
    c_close = sub_c[-1]
    c_high = sub_h[-1]
    c_low = sub_l[-1]
    span = c_high - c_low
    if span <= 0:
        return False, 0.0, 0.0

    body = abs(c_close - c_open)
    body_ratio = body / span

    if direction == "BUY":
        rejection_wick = min(c_open, c_close) - c_low
        wick_ratio = rejection_wick / span
        directional_close = (c_close > c_open) and (c_close > level)
    else:
        rejection_wick = c_high - max(c_open, c_close)
        wick_ratio = rejection_wick / span
        directional_close = (c_close < c_open) and (c_close < level)

    is_valid_crt = bool(directional_close and body_ratio >= 0.40 and wick_ratio >= 0.25)
    return is_valid_crt, body_ratio, wick_ratio


def build_d1_storyline_cache(df_d1: pd.DataFrame) -> dict:
    cache = {}
    n_days = len(df_d1)
    atr_series = compute_atr(df_d1, 14)
    
    for i in range(15, n_days):
        sub_d1 = df_d1.iloc[:i]
        levels = av_levels(sub_d1)
        prev_bar = sub_d1.iloc[-1]
        bias = "BUY" if prev_bar["close"] > prev_bar["open"] else "SELL"
        cur_atr = float(atr_series.iloc[i - 1]) if not pd.isna(atr_series.iloc[i - 1]) else 0.0
        
        d1_date = sub_d1.iloc[-1]["time"].date()
        cache[d1_date] = {
            "levels": levels,
            "atr": cur_atr,
            "bias": bias,
            "close": float(prev_bar["close"]),
        }
    return cache


def build_h1_cache(
    df_h1: pd.DataFrame,
    df_m15: pd.DataFrame,
    days: int,
) -> tuple[dict, np.ndarray, np.ndarray]:
    h1_close_times = (df_h1["time"].dt.tz_localize(None) + pd.Timedelta(hours=1)).values.astype("datetime64[ns]")
    m15_times_naive = df_m15["time"].dt.tz_localize(None).values.astype("datetime64[ns]")

    end_time = df_m15["time"].iloc[-1]
    start_time = end_time - pd.Timedelta(days=days)

    start_h1_cut = max(25, int(np.searchsorted(h1_close_times, np.datetime64(start_time.tz_localize(None)), side="left")) - 40)
    
    h1_cache = {}
    for h1_cut in range(start_h1_cut, len(df_h1) + 1):
        sub_h1 = df_h1.iloc[max(0, h1_cut - 60):h1_cut]
        last_bar = sub_h1.iloc[-1]
        c_atr = float(last_bar["atr"]) if not pd.isna(last_bar["atr"]) else 0.0
        c_adx = float(last_bar["adx"]) if not pd.isna(last_bar["adx"]) else 20.0
        if c_atr <= 0:
            continue
        lvls = av_levels(sub_h1)
        if not lvls:
            continue
        qm = quasimodo_candidates(sub_h1, radius=2)
        break_time_naive = (last_bar["time"].tz_localize(None) + pd.Timedelta(hours=1)).to_datetime64()
        break_m15_idx = int(np.searchsorted(m15_times_naive, break_time_naive, side="left"))
        h1_cache[h1_cut] = (sub_h1, last_bar, c_atr, c_adx, lvls, qm, break_m15_idx)

    return h1_cache, h1_close_times, m15_times_naive


def check_storyline(
    d1_cache: dict,
    current_time: pd.Timestamp,
    direction: str,
    current_price: float,
) -> bool:
    prev_date = (current_time - timedelta(days=1)).date()
    info = d1_cache.get(prev_date)
    if not info:
        return True

    levels = info["levels"]
    atr_d1 = info["atr"]
    
    if direction == "BUY":
        opp_resistances = [
            lvl["level"] for lvl in levels
            if lvl["type"] == "A_RESISTANCE" and lvl["level"] >= current_price
        ]
        if opp_resistances and atr_d1 > 0:
            nearest_res = min(opp_resistances)
            dist_atr = (nearest_res - current_price) / atr_d1
            if dist_atr < 0.80:
                return False
    else:
        opp_supports = [
            lvl["level"] for lvl in levels
            if lvl["type"] == "V_SUPPORT" and lvl["level"] <= current_price
        ]
        if opp_supports and atr_d1 > 0:
            nearest_sup = max(opp_supports)
            dist_atr = (current_price - nearest_sup) / atr_d1
            if dist_atr < 0.80:
                return False

    return True


def simulate_trade(
    direction: str,
    entry: float,
    sl: float,
    tp1: float,
    tp2: float,
    highs: np.ndarray,
    lows: np.ndarray,
    closes: np.ndarray,
    opens: np.ndarray,
    spread: float,
    max_hold_bars: int = 160,
) -> tuple[float, str, int]:
    risk = abs(entry - sl)
    if risk <= 0 or len(highs) == 0:
        return 0.0, "NO_DATA", 0

    sign = 1 if direction == "BUY" else -1
    tp1_rr = sign * (tp1 - entry) / risk
    tp2_rr = sign * (tp2 - entry) / risk

    leg1_done = False
    be_buffer = spread * 1.5
    be_price = entry + be_buffer if direction == "BUY" else entry - be_buffer

    n_bars = min(len(highs), max_hold_bars)
    for i in range(n_bars):
        shift = spread if direction == "SELL" else 0.0
        h = highs[i] + shift
        l = lows[i] + shift
        o = opens[i] + shift
        c = closes[i] + shift

        active_sl = be_price if leg1_done else sl

        # Comprobar Gap adverso en apertura
        if sign * (o - active_sl) <= 0:
            slip_rr = sign * (o - entry) / risk
            total_rr = (0.5 * tp1_rr) + (0.5 * slip_rr) if leg1_done else slip_rr
            return total_rr, "GAP_SL", i + 1

        if direction == "BUY":
            hit_sl = l <= active_sl
            hit_tp1 = h >= tp1
            hit_tp2 = h >= tp2
        else:
            hit_sl = h >= active_sl
            hit_tp1 = l <= tp1
            hit_tp2 = l <= tp2

        if not leg1_done:
            if hit_sl:
                return -1.0, "FULL_SL", i + 1
            if hit_tp1:
                leg1_done = True
                if hit_tp2:
                    return (0.5 * tp1_rr) + (0.5 * tp2_rr), "FULL_TP", i + 1
                hit_reversal_be = (l <= be_price) if direction == "BUY" else (h >= be_price)
                if hit_reversal_be:
                    return (0.5 * tp1_rr) + 0.0, "TP1_BE", i + 1
        else:
            if hit_sl:
                return (0.5 * tp1_rr) + 0.0, "TP1_BE", i + 1
            if hit_tp2:
                return (0.5 * tp1_rr) + (0.5 * tp2_rr), "FULL_TP", i + 1

    exit_c = closes[n_bars - 1] + (spread if direction == "SELL" else 0.0)
    remain_rr = sign * (exit_c - entry) / risk
    total_rr = (0.5 * tp1_rr) + (0.5 * remain_rr) if leg1_done else remain_rr
    return total_rr, "TIMEOUT", n_bars


def run_single_symbol_replay_fast(
    symbol: str,
    frames: dict[str, pd.DataFrame],
    d1_cache: dict,
    h1_cache: dict,
    h1_close_times: np.ndarray,
    m15_times_naive: np.ndarray,
    days: int = 730,
    variant: str = "BASELINE",
) -> list[dict]:
    df_m15 = frames["M15"]

    spread = SPREADS.get(symbol, 0.00015)
    is_synth = IS_SYNTH_MAP.get(symbol, "SYNTH" in str(ASSET_CATEGORIES.get(symbol, "")).upper() or "BOOM" in str(ASSET_CATEGORIES.get(symbol, "")).upper() or "CRASH" in str(ASSET_CATEGORIES.get(symbol, "")).upper() or "STEP" in str(ASSET_CATEGORIES.get(symbol, "")).upper() or "JUMP" in str(ASSET_CATEGORIES.get(symbol, "")).upper() or "VOL" in str(ASSET_CATEGORIES.get(symbol, "")).upper())

    end_time = df_m15["time"].iloc[-1]
    start_time = end_time - pd.Timedelta(days=days)

    start_m15_idx = int(np.searchsorted(df_m15["time"].values, np.datetime64(start_time)))
    start_m15_idx = max(40, start_m15_idx)

    m15_times = df_m15["time"].values
    m15_opens = df_m15["open"].values.astype(float)
    m15_highs = df_m15["high"].values.astype(float)
    m15_lows = df_m15["low"].values.astype(float)
    m15_closes = df_m15["close"].values.astype(float)

    n_m15 = len(df_m15)
    trades = []
    busy_until_idx = -1

    for m_idx in range(start_m15_idx, n_m15 - 2):
        if m_idx <= busy_until_idx:
            continue

        now_np = m15_times_naive[m_idx]
        now_ts = pd.Timestamp(m15_times[m_idx])

        # Filtro de Killzones en activos tradicionales
        if not is_synth:
            t_hour = now_ts.hour + (now_ts.minute / 60.0)
            in_london = (7.0 <= t_hour <= 11.0)
            in_ny = (12.5 <= t_hour <= 17.0)
            if variant in ("AUGMENTED", "SELECTIVE") and not (in_london or in_ny):
                continue

        h1_cut = int(np.searchsorted(h1_close_times, now_np, side="right"))
        if h1_cut < 25:
            continue

        h1_entry = h1_cache.get(h1_cut)
        if not h1_entry:
            continue

        cached_closed_h1, cached_last_h1, cached_atr, cached_adx, cached_levels_h1, cached_qm_list, cached_break_m15_idx = h1_entry

        if m_idx < cached_break_m15_idx:
            continue
        m15_bars_count = (m_idx - cached_break_m15_idx) + 1
        if m15_bars_count < 1 or m15_bars_count > 8:
            continue

        sub_o = m15_opens[cached_break_m15_idx : m_idx + 1]
        sub_h = m15_highs[cached_break_m15_idx : m_idx + 1]
        sub_l = m15_lows[cached_break_m15_idx : m_idx + 1]
        sub_c = m15_closes[cached_break_m15_idx : m_idx + 1]

        candidate_signal = None

        # 1. Quasimodo Estructural (ESC_3_QUASIMODO)
        for qm in cached_qm_list:
            q_dir = qm["direction"]
            q_shoulder = qm["shoulder"]
            q_head = qm["head"]

            if variant == "BASELINE":
                tol = 0.35 * cached_atr
                touches = bool(np.any((sub_l <= q_shoulder + tol) & (sub_h >= q_shoulder - tol)))
                last_m_close = sub_c[-1]
                last_m_open = sub_o[-1]
                sign = 1 if q_dir == "BUY" else -1
                dist = sign * (last_m_close - q_shoulder)
                retest_ok = bool(touches and 0 <= dist <= 0.50 * cached_atr and sign * (last_m_close - last_m_open) > 0)
            else:
                retest_ok, _, _ = evaluate_crt_m15_rejection_np(sub_o, sub_h, sub_l, sub_c, q_shoulder, q_dir, cached_atr, 0.35)

            if not retest_ok:
                continue

            sign = 1 if q_dir == "BUY" else -1
            if (q_dir == "BUY" and np.min(sub_l) <= q_head) or (q_dir == "SELL" and np.max(sub_h) >= q_head):
                continue

            candidate_signal = {
                "scenario": "ESC_3_QUASIMODO",
                "direction": q_dir,
                "ref_level": q_shoulder,
                "stop_loss": q_head - (sign * 0.10 * cached_atr),
            }
            break

        # 2. Fractalidad 3 velas (ESC_3_FRACTAL)
        if candidate_signal is None and len(cached_closed_h1) >= 4:
            p2 = cached_closed_h1.iloc[-3]
            p1 = cached_closed_h1.iloc[-2]
            p0 = cached_last_h1

            f_dir = None
            f_neckline = None
            if p1["low"] < p2["low"] and p0["close"] > p0["open"] and p0["close"] > p2["high"]:
                f_dir, f_neckline = "BUY", float(p2["high"])
            elif p1["high"] > p2["high"] and p0["close"] < p0["open"] and p0["close"] < p2["low"]:
                f_dir, f_neckline = "SELL", float(p2["low"])

            if f_dir:
                span_p0 = p0["high"] - p0["low"]
                body_p0 = abs(p0["close"] - p0["open"])
                if span_p0 > 0 and (body_p0 / span_p0) >= 0.55:
                    if variant == "BASELINE":
                        tol = 0.35 * cached_atr
                        touches = bool(np.any((sub_l <= f_neckline + tol) & (sub_h >= f_neckline - tol)))
                        last_m_close = sub_c[-1]
                        last_m_open = sub_o[-1]
                        sign = 1 if f_dir == "BUY" else -1
                        dist = sign * (last_m_close - f_neckline)
                        retest_ok = bool(touches and 0 <= dist <= 0.40 * cached_atr and sign * (last_m_close - last_m_open) > 0)
                    else:
                        retest_ok, _, _ = evaluate_crt_m15_rejection_np(sub_o, sub_h, sub_l, sub_c, f_neckline, f_dir, cached_atr, 0.35)

                    if retest_ok:
                        sign = 1 if f_dir == "BUY" else -1
                        sl = (min(float(np.min(sub_l)), float(p0["low"])) - 0.15 * cached_atr if f_dir == "BUY"
                              else max(float(np.max(sub_h)), float(p0["high"])) + 0.15 * cached_atr)
                        candidate_signal = {
                            "scenario": "ESC_3_FRACTAL",
                            "direction": f_dir,
                            "ref_level": f_neckline,
                            "stop_loss": sl,
                        }

        # 3. Continuación Clásica Fresh (ESC_1_CONTINUATION) solo en Augmented con ADX >= 22
        if candidate_signal is None and variant in ("AUGMENTED", "SELECTIVE") and cached_adx >= 22.0:
            for lvl in reversed(cached_levels_h1[-15:]):
                l_dir = "BUY" if lvl["type"] == "A_RESISTANCE" else "SELL"
                if not level_is_fresh(cached_closed_h1, lvl):
                    continue
                sign = 1 if l_dir == "BUY" else -1
                if sign * (cached_last_h1["close"] - lvl["level"]) <= 0:
                    continue

                retest_ok, _, _ = evaluate_crt_m15_rejection_np(sub_o, sub_h, sub_l, sub_c, lvl["level"], l_dir, cached_atr, 0.35)
                if retest_ok:
                    sl = (min(float(np.min(sub_l)), float(cached_last_h1["low"])) - 0.15 * cached_atr if l_dir == "BUY"
                          else max(float(np.max(sub_h)), float(cached_last_h1["high"])) + 0.15 * cached_atr)
                    candidate_signal = {
                        "scenario": "ESC_1_CONTINUATION_CRT",
                        "direction": l_dir,
                        "ref_level": lvl["level"],
                        "stop_loss": sl,
                    }
                    break

        if candidate_signal is None:
            continue

        direction = candidate_signal["direction"]
        sl = candidate_signal["stop_loss"]
        scenario = candidate_signal["scenario"]

        if not is_direction_allowed(symbol, direction):
            continue

        if m_idx + 1 >= n_m15:
            continue

        fill_price = m15_opens[m_idx + 1] + (spread if direction == "BUY" else 0.0)
        sign = 1 if direction == "BUY" else -1
        risk = sign * (fill_price - sl)

        if risk <= 0 or (spread > 0 and risk < (1.5 * spread)):
            continue

        if variant in ("AUGMENTED", "SELECTIVE"):
            if not check_storyline(d1_cache, now_ts, direction, fill_price):
                continue

            opp_levels = [
                l["level"] for l in cached_levels_h1
                if l["type"] == ("A_RESISTANCE" if direction == "BUY" else "V_SUPPORT")
                and sign * (l["level"] - fill_price) > 0
            ]
            if opp_levels:
                nearest_obs = min(opp_levels) if direction == "BUY" else max(opp_levels)
                space_rr = abs(nearest_obs - fill_price) / risk
                if space_rr < 2.0:
                    continue
        else:
            prev_d1_date = (now_ts - timedelta(days=1)).date()
            d1_info = d1_cache.get(prev_d1_date)
            if d1_info and d1_info["bias"] != direction:
                continue

        tp1_price = fill_price + sign * (2.0 * risk)
        runner_rr = 4.0 if cached_adx >= 28.0 else (3.0 if cached_adx >= 22.0 else 2.5)
        tp2_price = fill_price + sign * (runner_rr * risk)

        future_h = m15_highs[m_idx + 1:]
        future_l = m15_lows[m_idx + 1:]
        future_c = m15_closes[m_idx + 1:]
        future_o = m15_opens[m_idx + 1:]

        rr_result, outcome, bars_held = simulate_trade(
            direction=direction,
            entry=fill_price,
            sl=sl,
            tp1=tp1_price,
            tp2=tp2_price,
            highs=future_h,
            lows=future_l,
            closes=future_c,
            opens=future_o,
            spread=spread,
            max_hold_bars=160,
        )

        busy_until_idx = m_idx + bars_held
        risk_usd = 100.0
        pnl_usd = risk_usd * rr_result

        trades.append({
            "symbol": symbol,
            "category": ASSET_CATEGORIES.get(symbol, "OTHER"),
            "variant": variant,
            "time": str(now_ts),
            "direction": direction,
            "scenario": scenario,
            "entry_price": round(fill_price, 5),
            "stop_loss": round(sl, 5),
            "risk_dist": round(risk, 5),
            "tp1_price": round(tp1_price, 5),
            "tp2_price": round(tp2_price, 5),
            "outcome": outcome,
            "rr": round(rr_result, 3),
            "pnl_usd": round(pnl_usd, 2),
            "is_win": bool(rr_result > 0),
            "is_tp1": bool(outcome in ("TP1_BE", "FULL_TP")),
            "is_tp2": bool(outcome == "FULL_TP"),
            "bars_held": bars_held,
        })

    return trades


def process_symbol_worker(sym: str, days: int = 730) -> tuple[dict, list[dict], list[dict]] | None:
    t0_sym = time.time()
    frames = load_dataset(sym)
    if frames is None:
        return None

    frames["H1"]["atr"] = compute_atr(frames["H1"], 14)
    frames["H1"]["adx"] = compute_adx(frames["H1"], 14)

    d1_cache = build_d1_storyline_cache(frames["D1"])
    h1_cache, h1_close_times, m15_times_naive = build_h1_cache(frames["H1"], frames["M15"], days)

    tr_base = run_single_symbol_replay_fast(
        sym, frames, d1_cache, h1_cache, h1_close_times, m15_times_naive, days=days, variant="BASELINE"
    )
    tr_aug = run_single_symbol_replay_fast(
        sym, frames, d1_cache, h1_cache, h1_close_times, m15_times_naive, days=days, variant="AUGMENTED"
    )

    n_b = len(tr_base)
    wr_b = (sum(1 for t in tr_base if t["is_win"]) / n_b * 100.0) if n_b > 0 else 0.0
    r_b = sum(t["rr"] for t in tr_base)
    exp_b = (r_b / n_b) if n_b > 0 else 0.0

    n_a = len(tr_aug)
    wr_a = (sum(1 for t in tr_aug if t["is_win"]) / n_a * 100.0) if n_a > 0 else 0.0
    r_a = sum(t["rr"] for t in tr_aug)
    exp_a = (r_a / n_a) if n_a > 0 else 0.0

    elapsed_sym = time.time() - t0_sym

    metrics = {
        "symbol": sym,
        "category": ASSET_CATEGORIES.get(sym, "OTHER"),
        "trades_baseline": n_b,
        "wr_baseline": round(wr_b, 1),
        "exp_baseline": round(exp_b, 3),
        "total_r_baseline": round(r_b, 2),
        "trades_augmented": n_a,
        "wr_augmented": round(wr_a, 1),
        "exp_augmented": round(exp_a, 3),
        "total_r_augmented": round(r_a, 2),
        "wr_diff": round(wr_a - wr_b, 1),
        "r_diff": round(r_a - r_b, 2),
        "elapsed": round(elapsed_sym, 1),
    }

    return metrics, tr_base, tr_aug


def run_full_2year_audit(days: int = 730):
    from concurrent.futures import ProcessPoolExecutor, as_completed

    print("=" * 115, flush=True)
    print(f"AUDITORÍA CIENTÍFICA REPLAY DE 2 AÑOS (730 DÍAS): MALAYSIAN SNR", flush=True)
    print("Comparativa directa:", flush=True)
    print("  Variante A [BASELINE]  : Malaysian SNR Actual (H1/M15, D1 lineal verde/rojo, retest pasivo)", flush=True)
    print("  Variante B [AUGMENTED] : Malaysian SNR Mejorado (Storyline D1 A/V, CRT Sweep+Rejection M15, Obstáculo >= 2R)", flush=True)
    print("=" * 115, flush=True)

    symbols = list(ASSET_CATEGORIES.keys())
    all_trades_baseline = []
    all_trades_augmented = []
    symbol_metrics = []

    t0_global = time.time()

    with ProcessPoolExecutor(max_workers=8) as executor:
        futures = {executor.submit(process_symbol_worker, sym, days): sym for sym in symbols}
        done_count = 0
        for fut in as_completed(futures):
            res = fut.result()
            if res is None:
                continue
            done_count += 1
            met, tr_b, tr_a = res
            all_trades_baseline.extend(tr_b)
            all_trades_augmented.extend(tr_a)
            symbol_metrics.append(met)
            s = met["symbol"]
            print(f"[{done_count:02d}/{len(symbols)}] {s:<20} | Base: {met['trades_baseline']:3d} trd (WR: {met['wr_baseline']:4.1f}%, {met['total_r_baseline']:+6.1f}R) | Augm: {met['trades_augmented']:3d} trd (WR: {met['wr_augmented']:4.1f}%, {met['total_r_augmented']:+6.1f}R) -> Delta WR: {met['wr_diff']:+4.1f}% [{met['elapsed']}s]", flush=True)

    total_elapsed = time.time() - t0_global

    out_dir = PROJECT_ROOT / "storage" / "analysis" / "msnr_2year_audit"
    out_dir.mkdir(parents=True, exist_ok=True)

    df_sym = pd.DataFrame(symbol_metrics)
    df_sym.to_csv(out_dir / "symbols_comparison.csv", index=False)

    df_tr_base = pd.DataFrame(all_trades_baseline)
    df_tr_aug = pd.DataFrame(all_trades_augmented)
    if not df_tr_base.empty:
        df_tr_base.to_csv(out_dir / "trades_baseline.csv", index=False)
    if not df_tr_aug.empty:
        df_tr_aug.to_csv(out_dir / "trades_augmented.csv", index=False)

    def calc_global_stats(trades):
        if not trades:
            return {"trades": 0, "win_rate": 0.0, "tp1_rate": 0.0, "tp2_rate": 0.0,
                    "expectancy_r": 0.0, "total_r": 0.0, "profit_factor": 0.0, "max_drawdown_r": 0.0}
        n = len(trades)
        wins = sum(1 for t in trades if t["is_win"])
        tp1s = sum(1 for t in trades if t["is_tp1"])
        tp2s = sum(1 for t in trades if t["is_tp2"])
        r_vals = np.array([t["rr"] for t in trades])
        tot_r = float(np.sum(r_vals))
        mean_r = float(np.mean(r_vals))

        pos_r = float(np.sum(r_vals[r_vals > 0]))
        neg_r = float(abs(np.sum(r_vals[r_vals < 0])))
        pf = (pos_r / neg_r) if neg_r > 0 else 999.0

        cum = np.r_[0.0, np.cumsum(r_vals)]
        dd = float(np.max(np.maximum.accumulate(cum) - cum))

        return {
            "trades": n,
            "win_rate": round(wins / n * 100.0, 2),
            "tp1_rate": round(tp1s / n * 100.0, 2),
            "tp2_rate": round(tp2s / n * 100.0, 2),
            "expectancy_r": round(mean_r, 4),
            "total_r": round(tot_r, 2),
            "profit_factor": round(pf, 2),
            "max_drawdown_r": round(dd, 2),
        }

    stats_b = calc_global_stats(all_trades_baseline)
    stats_a = calc_global_stats(all_trades_augmented)

    summary_report = {
        "days": days,
        "elapsed_seconds": round(total_elapsed, 1),
        "baseline": stats_b,
        "augmented": stats_a,
        "delta": {
            "win_rate_diff": round(stats_a["win_rate"] - stats_b["win_rate"], 2),
            "expectancy_diff": round(stats_a["expectancy_r"] - stats_b["expectancy_r"], 4),
            "total_r_diff": round(stats_a["total_r"] - stats_b["total_r"], 2),
            "profit_factor_diff": round(stats_a["profit_factor"] - stats_b["profit_factor"], 2),
            "drawdown_reduction": round(stats_b["max_drawdown_r"] - stats_a["max_drawdown_r"], 2),
        }
    }

    with open(out_dir / "audit_metrics.json", "w", encoding="utf-8") as f:
        json.dump(summary_report, f, indent=2)

    # Guardar resumen maestro consolidado en storage/analysis
    summary_60_csv = PROJECT_ROOT / "storage" / "analysis" / "replay_malaysian_snr_60_assets_2y_summary.csv"
    df_sym.to_csv(summary_60_csv, index=False)

    print("\n" + "=" * 115, flush=True)
    print(f"RESUMEN GLOBAL CONSOLIDADO (2 AÑOS - {len(symbols)} ACTIVOS) [Ejecutado en {total_elapsed:.1f}s]", flush=True)
    print("=" * 115, flush=True)
    print(f"{'MÉTRICA':<30} | {'BASELINE (ACTUAL)':<22} | {'AUGMENTED (MEJORADO)':<22} | {'DIFERENCIA / DELTA'}", flush=True)
    print("-" * 115, flush=True)
    print(f"{'Total Operaciones':<30} | {stats_b['trades']:<22d} | {stats_a['trades']:<22d} | {stats_a['trades'] - stats_b['trades']:+d} trades", flush=True)
    print(f"{'Win Rate Global (%)':<30} | {stats_b['win_rate']:>20.2f}% | {stats_a['win_rate']:>20.2f}% | {stats_a['win_rate'] - stats_b['win_rate']:>+18.2f}%", flush=True)
    print(f"{'Acierto TP1 (%)':<30} | {stats_b['tp1_rate']:>20.2f}% | {stats_a['tp1_rate']:>20.2f}% | {stats_a['tp1_rate'] - stats_b['tp1_rate']:>+18.2f}%", flush=True)
    print(f"{'Acierto TP2 Runner (%)':<30} | {stats_b['tp2_rate']:>20.2f}% | {stats_a['tp2_rate']:>20.2f}% | {stats_a['tp2_rate'] - stats_b['tp2_rate']:>+18.2f}%", flush=True)
    print(f"{'Expectativa (R/trade)':<30} | {stats_b['expectancy_r']:>20.4f}R | {stats_a['expectancy_r']:>20.4f}R | {stats_a['expectancy_r'] - stats_b['expectancy_r']:>+18.4f}R", flush=True)
    print(f"{'Resultado Total (R)':<30} | {stats_b['total_r']:>20.2f}R | {stats_a['total_r']:>20.2f}R | {stats_a['total_r'] - stats_b['total_r']:>+18.2f}R", flush=True)
    print(f"{'Profit Factor':<30} | {stats_b['profit_factor']:>22.2f} | {stats_a['profit_factor']:>22.2f} | {stats_a['profit_factor'] - stats_b['profit_factor']:>+19.2f}", flush=True)
    print(f"{'Max Drawdown (R)':<30} | {stats_b['max_drawdown_r']:>20.2f}R | {stats_a['max_drawdown_r']:>20.2f}R | {stats_a['max_drawdown_r'] - stats_b['max_drawdown_r']:>+18.2f}R", flush=True)
    print("=" * 115, flush=True)

    print("\n" + "=" * 115, flush=True)
    print("DESGLOSE POR CATEGORÍA DE ACTIVO", flush=True)
    print("=" * 115, flush=True)
    print(f"{'CATEGORÍA':<15} | {'TRD BASE':<10} | {'WR BASE':<10} | {'R BASE':<10} | {'TRD AUG':<10} | {'WR AUG':<10} | {'R AUG':<10} | {'DELTA WR'}", flush=True)
    print("-" * 115, flush=True)
    for cat in sorted(df_sym["category"].unique()):
        sub = df_sym[df_sym["category"] == cat]
        if sub.empty:
            continue
        tb = int(sub["trades_baseline"].sum())
        ta = int(sub["trades_augmented"].sum())
        wrb = (sub["trades_baseline"] * sub["wr_baseline"]).sum() / tb if tb > 0 else 0.0
        wra = (sub["trades_augmented"] * sub["wr_augmented"]).sum() / ta if ta > 0 else 0.0
        rb = float(sub["total_r_baseline"].sum())
        ra = float(sub["total_r_augmented"].sum())
        print(f"{cat:<15} | {tb:<10d} | {wrb:>8.1f}% | {rb:>+8.1f}R | {ta:<10d} | {wra:>8.1f}% | {ra:>+8.1f}R | {wra - wrb:>+8.1f}%", flush=True)
    print("=" * 115, flush=True)

    # Ranking y Clasificación Cuantitativa de todos los activos
    df_aug = df_sym.sort_values(by="total_r_augmented", ascending=False)
    print("\n" + "=" * 115, flush=True)
    print("RANKING COMPLETO DE ACTIVOS EVALUADOS (ORDENADO POR R TOTAL AUGMENTED)", flush=True)
    print("=" * 115, flush=True)
    print(f"{'SÍMBOLO':<24} | {'CATEGORÍA':<14} | {'TRADES':<7} | {'WR AUG (%)':<11} | {'TOTAL R':<10} | {'EXP (R)':<9} | {'ESTADO RECOMENDADO'}", flush=True)
    print("-" * 115, flush=True)
    for _, r in df_aug.iterrows():
        ta = int(r["trades_augmented"])
        wra = float(r["wr_augmented"])
        tra = float(r["total_r_augmented"])
        expa = float(r["exp_augmented"])
        
        if tra > 0 and wra >= 33.3:
            rec = "AGREGAR / MANTENER ACTIVO (RENTABLE)"
        elif ta == 0:
            rec = "SIN SEÑALES / RECHAZO FILTROS D1"
        else:
            rec = "PODAR / DESACTIVAR (EXPECTATIVA NEGATIVA)"
        print(f"{r['symbol']:<24} | {r['category']:<14} | {ta:<7d} | {wra:>9.1f}% | {tra:>+8.2f}R | {expa:>+7.3f}R | {rec}", flush=True)
    print("=" * 115, flush=True)



if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--days", type=int, default=730)
    args = parser.parse_args()
    run_full_2year_audit(days=args.days)
