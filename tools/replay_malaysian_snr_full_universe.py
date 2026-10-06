"""Replay Histórico Cuantitativo y Multi-Activo: Estrategia Malaysian SNR (2 AÑOS COMPLETOS)
========================================================================================
Evalúa la metodología Malaysian SNR en TODOS los 60 activos (Disponibles y en PODA)
durante 730 días (24 meses completos: Octubre 2024 - Octubre 2026).

Motor ultra-optimizado con NumPy Vectorizado y Binary Search para evaluar millones de cotizaciones
en tiempo récord.
"""

import sys
import os
from pathlib import Path
from datetime import datetime, timezone, timedelta
from collections import defaultdict
import json
import argparse
import time

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Configuración UTF-8 en Windows
for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

import numpy as np
import pandas as pd
import MetaTrader5 as mt5

from config.symbol_policy import is_direction_allowed

# =====================================================================
# UNIVERSO COMPLETO DE ACTIVOS: DISPONIBLES (CORE) Y EN PODA (60 ACTIVOS)
# =====================================================================
ASSET_UNIVERSE = {
    # 1. FOREX CORE (Disponibles)
    "EURUSD": {"category": "FOREX_CORE", "status": "ACTIVE", "base_spread": 0.00014, "is_synth": False},
    "GBPUSD": {"category": "FOREX_CORE", "status": "ACTIVE", "base_spread": 0.00018, "is_synth": False},
    "USDJPY": {"category": "FOREX_CORE", "status": "ACTIVE", "base_spread": 0.015, "is_synth": False},
    "USDCAD": {"category": "FOREX_CORE", "status": "ACTIVE", "base_spread": 0.00018, "is_synth": False},
    "USDCHF": {"category": "FOREX_CORE", "status": "ACTIVE", "base_spread": 0.00016, "is_synth": False},
    "AUDUSD": {"category": "FOREX_CORE", "status": "ACTIVE", "base_spread": 0.00016, "is_synth": False},

    # 2. METALES, COMMODITIES, ÍNDICES & CRYPTO (Disponibles)
    "XAUUSD": {"category": "METALS", "status": "ACTIVE", "base_spread": 0.59, "is_synth": False},
    "XAGUSD": {"category": "METALS", "status": "ACTIVE", "base_spread": 0.055, "is_synth": False},
    "BTCUSD": {"category": "CRYPTO", "status": "ACTIVE", "base_spread": 18.5, "is_synth": False},
    "US Oil": {"category": "COMMODITIES", "status": "ACTIVE", "base_spread": 0.155, "is_synth": False},
    "US SP 500": {"category": "INDICES", "status": "ACTIVE", "base_spread": 0.36, "is_synth": False},
    "US Tech 100": {"category": "INDICES", "status": "ACTIVE", "base_spread": 0.90, "is_synth": False},
    "Wall Street 30": {"category": "INDICES", "status": "ACTIVE", "base_spread": 1.80, "is_synth": False},

    # 3. SINTÉTICOS CORE (Disponibles)
    "Step Index": {"category": "STEP_CORE", "status": "ACTIVE", "base_spread": 0.10, "is_synth": True},
    "Step Index 200": {"category": "STEP_CORE", "status": "ACTIVE", "base_spread": 0.20, "is_synth": True},
    "Step Index 500": {"category": "STEP_CORE", "status": "ACTIVE", "base_spread": 0.50, "is_synth": True},
    "Jump 10 Index": {"category": "JUMP_CORE", "status": "ACTIVE", "base_spread": 0.50, "is_synth": True},
    "Jump 25 Index": {"category": "JUMP_CORE", "status": "ACTIVE", "base_spread": 0.60, "is_synth": True},
    "Jump 50 Index": {"category": "JUMP_CORE", "status": "ACTIVE", "base_spread": 1.25, "is_synth": True},
    "Jump 100 Index": {"category": "JUMP_CORE", "status": "ACTIVE", "base_spread": 2.50, "is_synth": True},
    "Volatility 10 Index": {"category": "VOL_CORE", "status": "ACTIVE", "base_spread": 0.50, "is_synth": True},
    "Volatility 25 Index": {"category": "VOL_CORE", "status": "ACTIVE", "base_spread": 1.20, "is_synth": True},
    "Volatility 50 Index": {"category": "VOL_CORE", "status": "ACTIVE", "base_spread": 2.50, "is_synth": True},
    "Volatility 75 Index": {"category": "VOL_CORE", "status": "ACTIVE", "base_spread": 15.8, "is_synth": True},
    "Volatility 100 Index": {"category": "VOL_CORE", "status": "ACTIVE", "base_spread": 25.0, "is_synth": True},
    "Boom 1000 Index": {"category": "BOOM_CORE", "status": "ACTIVE", "base_spread": 1.75, "is_synth": True},
    "Boom 500 Index": {"category": "BOOM_CORE", "status": "ACTIVE", "base_spread": 1.20, "is_synth": True},
    "Boom 600 Index": {"category": "BOOM_CORE", "status": "ACTIVE", "base_spread": 1.40, "is_synth": True},
    "Crash 1000 Index": {"category": "CRASH_CORE", "status": "ACTIVE", "base_spread": 1.75, "is_synth": True},
    "Crash 500 Index": {"category": "CRASH_CORE", "status": "ACTIVE", "base_spread": 1.20, "is_synth": True},
    "Crash 600 Index": {"category": "CRASH_CORE", "status": "ACTIVE", "base_spread": 1.40, "is_synth": True},

    # 4. FOREX EN PODA (Pruned)
    "AUDCAD": {"category": "FOREX_PODA", "status": "PODA", "base_spread": 0.00022, "is_synth": False},
    "AUDCHF": {"category": "FOREX_PODA", "status": "PODA", "base_spread": 0.00022, "is_synth": False},
    "AUDJPY": {"category": "FOREX_PODA", "status": "PODA", "base_spread": 0.022, "is_synth": False},
    "AUDNZD": {"category": "FOREX_PODA", "status": "PODA", "base_spread": 0.00025, "is_synth": False},
    "CADCHF": {"category": "FOREX_PODA", "status": "PODA", "base_spread": 0.00022, "is_synth": False},
    "CADJPY": {"category": "FOREX_PODA", "status": "PODA", "base_spread": 0.022, "is_synth": False},
    "CHFJPY": {"category": "FOREX_PODA", "status": "PODA", "base_spread": 0.025, "is_synth": False},
    "EURAUD": {"category": "FOREX_PODA", "status": "PODA", "base_spread": 0.00024, "is_synth": False},
    "EURCAD": {"category": "FOREX_PODA", "status": "PODA", "base_spread": 0.00022, "is_synth": False},
    "EURCHF": {"category": "FOREX_PODA", "status": "PODA", "base_spread": 0.00020, "is_synth": False},
    "EURGBP": {"category": "FOREX_PODA", "status": "PODA", "base_spread": 0.00018, "is_synth": False},
    "EURJPY": {"category": "FOREX_PODA", "status": "PODA", "base_spread": 0.020, "is_synth": False},
    "EURNZD": {"category": "FOREX_PODA", "status": "PODA", "base_spread": 0.00028, "is_synth": False},
    "GBPAUD": {"category": "FOREX_PODA", "status": "PODA", "base_spread": 0.00028, "is_synth": False},
    "GBPCAD": {"category": "FOREX_PODA", "status": "PODA", "base_spread": 0.00026, "is_synth": False},
    "GBPCHF": {"category": "FOREX_PODA", "status": "PODA", "base_spread": 0.00025, "is_synth": False},
    "GBPJPY": {"category": "FOREX_PODA", "status": "PODA", "base_spread": 0.026, "is_synth": False},
    "GBPNZD": {"category": "FOREX_PODA", "status": "PODA", "base_spread": 0.00032, "is_synth": False},

    # 5. SINTÉTICOS EN PODA (Pruned)
    "Step Index 400": {"category": "SYNTH_PODA", "status": "PODA", "base_spread": 0.40, "is_synth": True},
    "Jump 75 Index": {"category": "SYNTH_PODA", "status": "PODA", "base_spread": 1.80, "is_synth": True},
    "Boom 900 Index": {"category": "SYNTH_PODA", "status": "PODA", "base_spread": 2.20, "is_synth": True},
    "Boom 300 Index": {"category": "SYNTH_PODA", "status": "PODA", "base_spread": 1.10, "is_synth": True},
    "Crash 900 Index": {"category": "SYNTH_PODA", "status": "PODA", "base_spread": 2.20, "is_synth": True},
    "Crash 300 Index": {"category": "SYNTH_PODA", "status": "PODA", "base_spread": 1.10, "is_synth": True},
    "Volatility 50 (1s) Index": {"category": "SYNTH_PODA", "status": "PODA", "base_spread": 3.00, "is_synth": True},
    "Volatility 75 (1s) Index": {"category": "SYNTH_PODA", "status": "PODA", "base_spread": 18.0, "is_synth": True},
    "Volatility 15 Index": {"category": "SYNTH_PODA", "status": "PODA", "base_spread": 1.50, "is_synth": True},
    "Volatility 90 Index": {"category": "SYNTH_PODA", "status": "PODA", "base_spread": 12.0, "is_synth": True},
    "Volatility 250 (1s) Index": {"category": "SYNTH_PODA", "status": "PODA", "base_spread": 35.0, "is_synth": True},
}


# =====================================================================
# INDICADORES AUXILIARES
# =====================================================================
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


def get_spread_multiplier(timestamp, is_synthetic: bool = False) -> float:
    if is_synthetic:
        return 1.0
    ts = pd.to_datetime(timestamp, utc=True)
    weekday = ts.weekday()
    hour = ts.hour
    minute = ts.minute
    t_float = hour + minute / 60.0

    # Cierre de fin de semana (Viernes 21:00 UTC a Domingo 21:00 UTC)
    if (weekday == 4 and t_float >= 21.0) or (weekday == 5) or (weekday == 6 and t_float < 21.0):
        return 4.0
    # Rollover nocturno (21:00 a 23:00 UTC)
    if 21.0 <= t_float < 23.0:
        return 3.0
    # Killzones Londres (07:00-10:00 UTC) y NY (12:00-16:00 UTC)
    if (7.0 <= t_float <= 10.0) or (12.0 <= t_float <= 16.0):
        return 1.0
    # Fuera de killzone (Asia / descanso)
    return 1.5


def is_market_open(timestamp, is_synthetic: bool = False) -> bool:
    if is_synthetic:
        return True
    ts = pd.to_datetime(timestamp, utc=True)
    weekday = ts.weekday()
    hour = ts.hour
    minute = ts.minute
    t_float = hour + minute / 60.0
    if (weekday == 4 and t_float >= 21.0) or (weekday == 5) or (weekday == 6 and t_float < 21.0):
        return False
    return True


# =====================================================================
# MOTOR DE DETECCIÓN: MALAYSIAN SNR (5 ESCENARIOS)
# =====================================================================
def detect_malaysian_snr_setups(df_h1: pd.DataFrame, symbol: str, is_synthetic: bool) -> list[dict]:
    df_h1 = df_h1.copy()
    df_h1["atr"] = compute_atr(df_h1, 14)
    df_h1["adx"] = compute_adx(df_h1, 14)

    h1_levels = []
    for i in range(2, len(df_h1) - 1):
        prev = df_h1.iloc[i - 1]
        curr = df_h1.iloc[i]

        # Patrón A (Resistencia): alcista seguida de bajista envolvente
        if prev["close"] > prev["open"] and curr["close"] < curr["open"]:
            if curr["close"] <= prev["open"]:
                h1_levels.append({
                    "type": "A_RESISTANCE",
                    "level": max(prev["high"], curr["high"]),
                    "break_level": prev["close"],
                    "time": curr["time"],
                    "idx": i,
                    "atr": curr["atr"],
                })
        # Patrón V (Soporte): bajista seguida de alcista envolvente
        elif prev["close"] < prev["open"] and curr["close"] > curr["open"]:
            if curr["close"] >= prev["open"]:
                h1_levels.append({
                    "type": "V_SUPPORT",
                    "level": min(prev["low"], curr["low"]),
                    "break_level": prev["close"],
                    "time": curr["time"],
                    "idx": i,
                    "atr": curr["atr"],
                })

    setups = []
    lvl_idx_map = {lvl["idx"]: lvl for lvl in h1_levels}
    h1_len = len(df_h1)

    for k in range(15, h1_len):
        candle = df_h1.iloc[k]
        c_time = candle["time"]
        if not is_market_open(c_time, is_synthetic):
            continue

        c_open = candle["open"]
        c_close = candle["close"]
        c_high = candle["high"]
        c_low = candle["low"]
        c_span = c_high - c_low
        if c_span <= 0:
            continue

        c_atr = candle["atr"] if not pd.isna(candle["atr"]) else c_span
        c_adx = candle["adx"] if not pd.isna(candle["adx"]) else 20.0

        # Revisar niveles activos recientes (entre 2 y 40 barras de antigüedad)
        recent_levels = [lvl for lvl in h1_levels if 2 < (k - lvl["idx"]) <= 40]

        for lvl in recent_levels:
            lvl_price = lvl["level"]
            break_price = lvl["break_level"]
            lvl_type = lvl["type"]

            if lvl_type == "A_RESISTANCE":
                body = c_close - c_open
                upper_wick = c_high - c_close
                # ESCENARIO 1: Ruptura Clásica (FRESH) -> BUY
                if c_close > lvl_price and (body / c_span) >= 0.50 and (upper_wick / c_span) <= 0.30:
                    if is_direction_allowed(symbol, "BUY"):
                        sl = c_low - (0.2 * c_atr)
                        risk = abs(break_price - sl)
                        if risk > 0:
                            setups.append({
                                "symbol": symbol,
                                "scenario": "ESC_1_CONTINUATION",
                                "direction": "BUY",
                                "time": c_time,
                                "entry_price": break_price,
                                "stop_loss": sl,
                                "risk_distance": risk,
                                "momentum_adx": c_adx,
                                "body_ratio": body / c_span,
                                "ref_level": lvl_price,
                            })
                            break
                # ESCENARIO 2: SNR Clásico (NO FRESH / Manipulación) -> SELL
                rejection_wick = c_high - max(c_open, c_close)
                if c_high > lvl_price and c_close <= lvl_price and (rejection_wick / c_span) >= 0.35:
                    if is_direction_allowed(symbol, "SELL"):
                        sl = c_high + (0.2 * c_atr)
                        risk = abs(c_close - sl)
                        if risk > 0:
                            setups.append({
                                "symbol": symbol,
                                "scenario": "ESC_2_REVERSAL",
                                "direction": "SELL",
                                "time": c_time,
                                "entry_price": c_close,
                                "stop_loss": sl,
                                "risk_distance": risk,
                                "momentum_adx": c_adx,
                                "body_ratio": abs(c_close - c_open) / c_span,
                                "ref_level": lvl_price,
                            })
                            break

            elif lvl_type == "V_SUPPORT":
                body = c_open - c_close
                lower_wick = c_close - c_low
                # ESCENARIO 1: Ruptura Clásica (FRESH) -> SELL
                if c_close < lvl_price and (body / c_span) >= 0.50 and (lower_wick / c_span) <= 0.30:
                    if is_direction_allowed(symbol, "SELL"):
                        sl = c_high + (0.2 * c_atr)
                        risk = abs(sl - break_price)
                        if risk > 0:
                            setups.append({
                                "symbol": symbol,
                                "scenario": "ESC_1_CONTINUATION",
                                "direction": "SELL",
                                "time": c_time,
                                "entry_price": break_price,
                                "stop_loss": sl,
                                "risk_distance": risk,
                                "momentum_adx": c_adx,
                                "body_ratio": body / c_span,
                                "ref_level": lvl_price,
                            })
                            break
                # ESCENARIO 2: SNR Clásico (NO FRESH / Manipulación) -> BUY
                rejection_wick = min(c_open, c_close) - c_low
                if c_low < lvl_price and c_close >= lvl_price and (rejection_wick / c_span) >= 0.35:
                    if is_direction_allowed(symbol, "BUY"):
                        sl = c_low - (0.2 * c_atr)
                        risk = abs(c_close - sl)
                        if risk > 0:
                            setups.append({
                                "symbol": symbol,
                                "scenario": "ESC_2_REVERSAL",
                                "direction": "BUY",
                                "time": c_time,
                                "entry_price": c_close,
                                "stop_loss": sl,
                                "risk_distance": risk,
                                "momentum_adx": c_adx,
                                "body_ratio": abs(c_close - c_open) / c_span,
                                "ref_level": lvl_price,
                            })
                            break

    # ESCENARIO 3: Fractalidad (HCH / Quiebre Rápido)
    for k in range(5, h1_len - 1):
        c_prev2 = df_h1.iloc[k - 2]
        c_prev1 = df_h1.iloc[k - 1]
        c_curr = df_h1.iloc[k]
        if not is_market_open(c_curr["time"], is_synthetic):
            continue

        if c_prev1["low"] < c_prev2["low"] and c_curr["close"] > c_curr["open"]:
            body = c_curr["close"] - c_curr["open"]
            span = c_curr["high"] - c_curr["low"]
            if span > 0 and (body / span) >= 0.55 and c_curr["close"] > c_prev2["high"]:
                if is_direction_allowed(symbol, "BUY"):
                    break_entry = c_prev1["close"]
                    sl = c_prev1["low"] - (0.15 * c_curr["atr"])
                    risk = abs(break_entry - sl)
                    if risk > 0:
                        setups.append({
                            "symbol": symbol,
                            "scenario": "ESC_3_FRACTAL",
                            "direction": "BUY",
                            "time": c_curr["time"],
                            "entry_price": break_entry,
                            "stop_loss": sl,
                            "risk_distance": risk,
                            "momentum_adx": c_curr["adx"],
                            "body_ratio": body / span,
                            "ref_level": c_prev2["high"],
                        })
        elif c_prev1["high"] > c_prev2["high"] and c_curr["close"] < c_curr["open"]:
            body = c_curr["open"] - c_curr["close"]
            span = c_curr["high"] - c_curr["low"]
            if span > 0 and (body / span) >= 0.55 and c_curr["close"] < c_prev2["low"]:
                if is_direction_allowed(symbol, "SELL"):
                    break_entry = c_prev1["close"]
                    sl = c_prev1["high"] + (0.15 * c_curr["atr"])
                    risk = abs(sl - break_entry)
                    if risk > 0:
                        setups.append({
                            "symbol": symbol,
                            "scenario": "ESC_3_FRACTAL",
                            "direction": "SELL",
                            "time": c_curr["time"],
                            "entry_price": break_entry,
                            "stop_loss": sl,
                            "risk_distance": risk,
                            "momentum_adx": c_curr["adx"],
                            "body_ratio": body / span,
                            "ref_level": c_prev2["low"],
                        })

    # ESCENARIO 5: Fair Value Gaps (FVG)
    for i in range(3, h1_len - 2):
        c0, c1, c2 = df_h1.iloc[i - 2], df_h1.iloc[i - 1], df_h1.iloc[i]
        if c2["low"] > c0["high"]:
            gap_top = c2["low"]
            gap_bot = c0["high"]
            gap_size = gap_top - gap_bot
            if gap_size > (0.1 * c2["atr"]):
                for f in range(i + 1, min(i + 12, h1_len)):
                    cf = df_h1.iloc[f]
                    if not is_market_open(cf["time"], is_synthetic):
                        continue
                    if cf["low"] <= gap_top and cf["close"] > gap_top:
                        if is_direction_allowed(symbol, "BUY"):
                            sl = gap_bot - (0.1 * gap_size)
                            risk = abs(cf["close"] - sl)
                            if risk > 0:
                                setups.append({
                                    "symbol": symbol,
                                    "scenario": "ESC_5_FVG_REBOUND",
                                    "direction": "BUY",
                                    "time": cf["time"],
                                    "entry_price": cf["close"],
                                    "stop_loss": sl,
                                    "risk_distance": risk,
                                    "momentum_adx": cf["adx"],
                                    "body_ratio": 0.6,
                                    "ref_level": gap_top,
                                })
                        break
                    elif cf["close"] < gap_bot:
                        if is_direction_allowed(symbol, "SELL"):
                            sl = gap_top + (0.1 * gap_size)
                            risk = abs(sl - gap_bot)
                            if risk > 0:
                                setups.append({
                                    "symbol": symbol,
                                    "scenario": "ESC_5_FVG_PIERCE",
                                    "direction": "SELL",
                                    "time": cf["time"],
                                    "entry_price": gap_bot,
                                    "stop_loss": sl,
                                    "risk_distance": risk,
                                    "momentum_adx": cf["adx"],
                                    "body_ratio": 0.7,
                                    "ref_level": gap_bot,
                                })
                        break

        elif c2["high"] < c0["low"]:
            gap_top = c0["low"]
            gap_bot = c2["high"]
            gap_size = gap_top - gap_bot
            if gap_size > (0.1 * c2["atr"]):
                for f in range(i + 1, min(i + 12, h1_len)):
                    cf = df_h1.iloc[f]
                    if not is_market_open(cf["time"], is_synthetic):
                        continue
                    if cf["high"] >= gap_bot and cf["close"] < gap_bot:
                        if is_direction_allowed(symbol, "SELL"):
                            sl = gap_top + (0.1 * gap_size)
                            risk = abs(sl - cf["close"])
                            if risk > 0:
                                setups.append({
                                    "symbol": symbol,
                                    "scenario": "ESC_5_FVG_REBOUND",
                                    "direction": "SELL",
                                    "time": cf["time"],
                                    "entry_price": cf["close"],
                                    "stop_loss": sl,
                                    "risk_distance": risk,
                                    "momentum_adx": cf["adx"],
                                    "body_ratio": 0.6,
                                    "ref_level": gap_bot,
                                })
                        break
                    elif cf["close"] > gap_top:
                        if is_direction_allowed(symbol, "BUY"):
                            sl = gap_bot - (0.1 * gap_size)
                            risk = abs(gap_top - sl)
                            if risk > 0:
                                setups.append({
                                    "symbol": symbol,
                                    "scenario": "ESC_5_FVG_PIERCE",
                                    "direction": "BUY",
                                    "time": cf["time"],
                                    "entry_price": gap_top,
                                    "stop_loss": sl,
                                    "risk_distance": risk,
                                    "momentum_adx": cf["adx"],
                                    "body_ratio": 0.7,
                                    "ref_level": gap_top,
                                })
                        break

    # Deduplicar señales cercanas (mínimo 3 horas de separación)
    setups = sorted(setups, key=lambda s: s["time"])
    deduped = []
    last_t = None
    for s in setups:
        if last_t is None or (s["time"] - last_t) >= timedelta(hours=3):
            deduped.append(s)
            last_t = s["time"]

    return deduped


# =====================================================================
# SIMULADOR ULTRA-RÁPIDO NUMPY DUAL-LEG ($10k, 1% RIESGO)
# =====================================================================
def simulate_dual_leg_fast(
    setup: dict,
    m15_times_np: np.ndarray,
    m15_highs: np.ndarray,
    m15_lows: np.ndarray,
    m15_closes: np.ndarray,
    base_spread: float,
    is_synthetic: bool,
    max_hold_bars: int = 160,
) -> dict | None:
    direction = setup["direction"]
    entry_price = float(setup["entry_price"])
    stop_loss = float(setup["stop_loss"])
    entry_time = setup["time"]
    symbol = setup["symbol"]
    scenario = setup["scenario"]
    adx = float(setup.get("momentum_adx", 20.0))
    body_ratio = float(setup.get("body_ratio", 0.6))
    risk_dist = float(setup["risk_distance"])

    if risk_dist <= 0:
        return None

    # Búsqueda binaria O(log N) del índice inicial en M15
    target_dt64 = np.datetime64(entry_time)
    start_idx = np.searchsorted(m15_times_np, target_dt64)
    n_bars = len(m15_times_np)
    if start_idx >= n_bars - 3:
        return None

    end_idx = min(n_bars, start_idx + max_hold_bars)

    # 1. ASIGNACIÓN DINÁMICA DE TARGETS SEGÚN CONTEXTO
    # TP1: Mínimo 1:2.0 RR (Requisito estricto)
    tp1_rr = 2.0
    tp1_price = entry_price + (2.0 * risk_dist) if direction == "BUY" else entry_price - (2.0 * risk_dist)

    # Evaluación contextual de la corredora
    if scenario in ["ESC_1_CONTINUATION", "ESC_5_FVG_PIERCE"] and adx >= 28.0 and body_ratio >= 0.65:
        runner_target_name = "TP4"
        tp2_rr = 5.0
    elif scenario in ["ESC_1_CONTINUATION", "ESC_3_FRACTAL", "ESC_5_FVG_PIERCE"] and adx >= 22.0:
        runner_target_name = "TP3"
        tp2_rr = 3.5
    else:
        runner_target_name = "TP2"
        tp2_rr = 2.5

    tp2_price = entry_price + (tp2_rr * risk_dist) if direction == "BUY" else entry_price - (tp2_rr * risk_dist)

    risk_usd_leg = 50.0  # 0.5% de $10,000 USD
    be_buffer = base_spread * 1.5
    be_price = entry_price + be_buffer if direction == "BUY" else entry_price - be_buffer

    leg1_closed = False
    leg1_outcome = None
    leg1_pnl_usd = 0.0
    leg1_rr = 0.0

    leg2_closed = False
    leg2_outcome = None
    leg2_pnl_usd = 0.0
    leg2_rr = 0.0
    leg2_in_be = False

    bars_held = 0
    max_mfe_r = 0.0
    max_mae_r = 0.0

    # Iteración NumPy ultrarrápida
    sub_highs = m15_highs[start_idx:end_idx]
    sub_lows = m15_lows[start_idx:end_idx]
    sub_closes = m15_closes[start_idx:end_idx]
    sub_times = m15_times_np[start_idx:end_idx]

    for bar_i in range(len(sub_highs)):
        bars_held = bar_i + 1
        high = sub_highs[bar_i]
        low = sub_lows[bar_i]
        close = sub_closes[bar_i]
        c_time = sub_times[bar_i]

        # Multiplicador dinámico de spread
        spread_mult = get_spread_multiplier(c_time, is_synthetic)
        eff_spread = base_spread * spread_mult

        if direction == "BUY":
            bar_mfe = (high - entry_price) / risk_dist
            bar_mae = (entry_price - low) / risk_dist
            hit_sl = low <= (stop_loss + eff_spread)
            hit_tp1 = high >= tp1_price
            hit_tp2 = high >= tp2_price
            hit_be = leg2_in_be and (low <= be_price)
        else:
            bar_mfe = (entry_price - low) / risk_dist
            bar_mae = (high - entry_price) / risk_dist
            hit_sl = high >= (stop_loss - eff_spread)
            hit_tp1 = low <= tp1_price
            hit_tp2 = low <= tp2_price
            hit_be = leg2_in_be and (high >= be_price)

        max_mfe_r = max(max_mfe_r, bar_mfe)
        max_mae_r = max(max_mae_r, bar_mae)

        # GESTIÓN PIERNA 1
        if not leg1_closed:
            if hit_sl and hit_tp1:
                hit_sl, hit_tp1 = True, False

            if hit_sl:
                leg1_closed = True
                leg1_outcome = "SL"
                leg1_rr = -1.0
                leg1_pnl_usd = -risk_usd_leg

                leg2_closed = True
                leg2_outcome = "SL"
                leg2_rr = -1.0
                leg2_pnl_usd = -risk_usd_leg
                break

            elif hit_tp1:
                leg1_closed = True
                leg1_outcome = "TP1"
                leg1_rr = tp1_rr
                leg1_pnl_usd = risk_usd_leg * tp1_rr  # +$100 (+1.0%)
                leg2_in_be = True

        # GESTIÓN PIERNA 2 (RUNNER)
        if leg1_closed and not leg2_closed:
            curr_sl = be_price if leg2_in_be else stop_loss
            be_sl_hit = (low <= curr_sl) if direction == "BUY" else (high >= curr_sl)

            if hit_tp2:
                leg2_closed = True
                leg2_outcome = runner_target_name
                leg2_rr = tp2_rr
                leg2_pnl_usd = risk_usd_leg * tp2_rr
                break
            elif be_sl_hit:
                leg2_closed = True
                leg2_outcome = "BE"
                leg2_rr = 0.0
                leg2_pnl_usd = 0.0
                break

    # Si expira por límite de barras
    if not leg1_closed:
        leg1_outcome = "TIMEOUT"
        pnl_diff = (close - entry_price) if direction == "BUY" else (entry_price - close)
        leg1_rr = max(-1.0, min(tp1_rr, pnl_diff / risk_dist))
        leg1_pnl_usd = risk_usd_leg * leg1_rr

    if not leg2_closed:
        leg2_outcome = "TIMEOUT_BE" if leg2_in_be else "TIMEOUT"
        pnl_diff = (close - entry_price) if direction == "BUY" else (entry_price - close)
        leg2_rr = max(0.0 if leg2_in_be else -1.0, min(tp2_rr, pnl_diff / risk_dist))
        leg2_pnl_usd = risk_usd_leg * leg2_rr

    total_pnl_usd = leg1_pnl_usd + leg2_pnl_usd
    total_rr = (leg1_rr * 0.5) + (leg2_rr * 0.5)
    trade_result = "WIN" if total_pnl_usd > 0 else ("BE" if total_pnl_usd == 0 else "LOSS")

    return {
        "symbol": symbol,
        "scenario": scenario,
        "direction": direction,
        "entry_time": str(entry_time),
        "entry_price": entry_price,
        "stop_loss": stop_loss,
        "risk_distance": risk_dist,
        "runner_target_name": runner_target_name,
        "tp1_price": tp1_price,
        "tp2_price": tp2_price,
        "bars_held": bars_held,
        "leg1_outcome": leg1_outcome,
        "leg1_pnl_usd": leg1_pnl_usd,
        "leg1_rr": leg1_rr,
        "leg2_outcome": leg2_outcome,
        "leg2_pnl_usd": leg2_pnl_usd,
        "leg2_rr": leg2_rr,
        "total_pnl_usd": total_pnl_usd,
        "total_rr": round(total_rr, 3),
        "trade_result": trade_result,
        "max_mfe_r": round(max_mfe_r, 2),
        "max_mae_r": round(max_mae_r, 2),
        "momentum_adx": round(adx, 1),
    }


# =====================================================================
# EJECUCIÓN MULTI-ACTIVO
# =====================================================================
def run_full_universe_replay(days: int = 730):
    print("=" * 115)
    print(f"REPLAY HISTÓRICO CUANTITATIVO 2 AÑOS COMPLETOS: ESTRATEGIA MALAYSIAN SNR ({days} DÍAS)")
    print("Capital: $10,000 USD | Riesgo: 1.0% ($100) en 2 Entradas de 50% ($50) | TP1 >= 1:2.0 RR | TP2/3/4 Contextual")
    print(f"Universo Completo: {len(ASSET_UNIVERSE)} Activos (Activos Disponibles + Activos en PODA)")
    print("=" * 115)

    if not mt5.initialize():
        print("[ERROR] No se pudo inicializar MetaTrader 5.")
        return

    now = datetime.now(timezone.utc)
    start_time = now - timedelta(days=days)

    all_trades = []
    asset_summaries = []

    t_start = time.time()

    for idx, (sym, meta) in enumerate(ASSET_UNIVERSE.items(), start=1):
        status = meta["status"]
        cat = meta["category"]
        base_spread = meta["base_spread"]
        is_synth = meta["is_synth"]

        print(f"[{idx:02d}/{len(ASSET_UNIVERSE)}] Analizando {sym:<22} [{status:<6} | {cat:<12}]...", end=" ", flush=True)

        mt5.symbol_select(sym, True)
        rates_h1 = mt5.copy_rates_range(sym, mt5.TIMEFRAME_H1, start_time, now)
        rates_m15 = mt5.copy_rates_range(sym, mt5.TIMEFRAME_M15, start_time, now)

        if rates_h1 is None or len(rates_h1) < 100 or rates_m15 is None or len(rates_m15) < 500:
            print("DATOS INSUFICIENTES (Omitido)")
            continue

        df_h1 = pd.DataFrame(rates_h1)
        df_h1["time"] = pd.to_datetime(df_h1["time"], unit="s", utc=True)

        df_m15 = pd.DataFrame(rates_m15)
        df_m15["time"] = pd.to_datetime(df_m15["time"], unit="s", utc=True)

        # Preparar arrays NumPy para máxima velocidad
        m15_times_np = df_m15["time"].values.astype("datetime64[ns]")
        m15_highs = df_m15["high"].values.astype(float)
        m15_lows = df_m15["low"].values.astype(float)
        m15_closes = df_m15["close"].values.astype(float)

        # Detectar setups de Malaysian SNR
        setups = detect_malaysian_snr_setups(df_h1, sym, is_synth)
        if not setups:
            print("0 setups")
            continue

        # Simular bar-a-bar con NumPy acelerado
        asset_trades = []
        for s in setups:
            res = simulate_dual_leg_fast(
                s, m15_times_np, m15_highs, m15_lows, m15_closes, base_spread, is_synth
            )
            if res:
                res["category"] = cat
                res["status"] = status
                asset_trades.append(res)
                all_trades.append(res)

        if not asset_trades:
            print("0 trades válidos")
            continue

        n_trades = len(asset_trades)
        wins = sum(1 for t in asset_trades if t["trade_result"] == "WIN")
        losses = sum(1 for t in asset_trades if t["trade_result"] == "LOSS")
        bes = sum(1 for t in asset_trades if t["trade_result"] == "BE")
        net_pnl = sum(t["total_pnl_usd"] for t in asset_trades)
        total_r = sum(t["total_rr"] for t in asset_trades)
        win_rate = (wins / n_trades) * 100.0 if n_trades > 0 else 0.0

        tp1_only = sum(1 for t in asset_trades if t["leg1_outcome"] == "TP1" and t["leg2_outcome"] == "BE")
        tp2_hits = sum(1 for t in asset_trades if t["leg2_outcome"] == "TP2")
        tp3_hits = sum(1 for t in asset_trades if t["leg2_outcome"] == "TP3")
        tp4_hits = sum(1 for t in asset_trades if t["leg2_outcome"] == "TP4")

        summary_row = {
            "symbol": sym,
            "status": status,
            "category": cat,
            "trades": n_trades,
            "wins": wins,
            "losses": losses,
            "bes": bes,
            "win_rate": round(win_rate, 1),
            "net_pnl_usd": round(net_pnl, 2),
            "return_pct": round((net_pnl / 10000.0) * 100.0, 2),
            "total_r": round(total_r, 2),
            "tp1_only_be": tp1_only,
            "tp2_hits": tp2_hits,
            "tp3_hits": tp3_hits,
            "tp4_hits": tp4_hits,
        }
        asset_summaries.append(summary_row)

        print(f"{n_trades:4d} trades | WR: {win_rate:4.1f}% | PnL: ${net_pnl:+9.1f} ({total_r:+6.1f}R)")

    mt5.shutdown()
    elapsed = time.time() - t_start

    print("\n" + "=" * 115)
    print(f"REPLAY DE 2 AÑOS COMPLETADO EN {elapsed:.1f} SEGUNDOS (~{elapsed/60:.1f} MINUTOS). GENERANDO AUDITORÍA...")
    print("=" * 115)

    output_dir = PROJECT_ROOT / "storage" / "analysis"
    output_dir.mkdir(parents=True, exist_ok=True)

    trades_df = pd.DataFrame(all_trades)
    trades_csv = output_dir / f"replay_malaysian_snr_2y_trades.csv"
    trades_df.to_csv(trades_csv, index=False)

    sum_df = pd.DataFrame(asset_summaries)
    sum_csv = output_dir / f"replay_malaysian_snr_2y_summary.csv"
    sum_df.to_csv(sum_csv, index=False)

    print(f"\n{'STATUS':<7} | {'CATEGORÍA':<12} | {'ACTIVO':<22} | {'TRADES':<6} | {'WIN RATE':<8} | {'PNL (USD)':<11} | {'RET (%)':<9} | {'RUNNERS (TP2/TP3/TP4)'}")
    print("-" * 115)

    sum_df = sum_df.sort_values(by="net_pnl_usd", ascending=False)
    for _, r in sum_df.iterrows():
        runners_str = f"TP2:{r['tp2_hits']} | TP3:{r['tp3_hits']} | TP4:{r['tp4_hits']} (BE:{r['tp1_only_be']})"
        print(f"{r['status']:<7} | {r['category']:<12} | {r['symbol']:<22} | {r['trades']:<6} | {r['win_rate']:>6.1f}% | ${r['net_pnl_usd']:>+9.2f} | {r['return_pct']:>+7.2f}% | {runners_str}")

    print("=" * 115)

    # Comparativa ACTIVE vs PODA
    active_mask = sum_df["status"] == "ACTIVE"
    poda_mask = sum_df["status"] == "PODA"

    active_pnl = sum_df[active_mask]["net_pnl_usd"].sum()
    poda_pnl = sum_df[poda_mask]["net_pnl_usd"].sum()

    active_trades = sum_df[active_mask]["trades"].sum()
    poda_trades = sum_df[poda_mask]["trades"].sum()

    active_wr = (sum_df[active_mask]["wins"].sum() / active_trades * 100.0) if active_trades > 0 else 0.0
    poda_wr = (sum_df[poda_mask]["wins"].sum() / poda_trades * 100.0) if poda_trades > 0 else 0.0

    print("\n" + "=" * 80)
    print("COMPARATIVA DE DESEMPEÑO A 2 AÑOS: ACTIVOS DISPONIBLES vs ACTIVOS EN PODA")
    print("=" * 80)
    print(f"ACTIVOS DISPONIBLES (ACTIVE) : {active_trades:5d} Trades | Win Rate: {active_wr:5.1f}% | PnL Neto: ${active_pnl:+11.2f} USD")
    print(f"ACTIVOS EN PODA (PRUNED)     : {poda_trades:5d} Trades | Win Rate: {poda_wr:5.1f}% | PnL Neto: ${poda_pnl:+11.2f} USD")
    print("-" * 80)
    alpha = active_pnl - poda_pnl
    print(f"ALPHA / PROTECCIÓN DE LA PODA: ${alpha:+11.2f} USD a favor de la selección activa.")
    print("=" * 80)

    # Desglose por escenario
    print("\n" + "=" * 80)
    print("DESGLOSE POR ESCENARIO OPERATIVO DE MALAYSIAN SNR (2 AÑOS)")
    print("=" * 80)
    scen_groups = trades_df.groupby("scenario")
    for sc_name, group in scen_groups:
        s_count = len(group)
        s_wins = sum(1 for _, t in group.iterrows() if t["trade_result"] == "WIN")
        s_wr = (s_wins / s_count) * 100.0 if s_count > 0 else 0.0
        s_pnl = group["total_pnl_usd"].sum()
        s_r = group["total_rr"].sum()
        print(f"{sc_name:<22}: {s_count:5d} trades | Win Rate: {s_wr:5.1f}% | PnL: ${s_pnl:+10.2f} ({s_r:+7.1f}R)")
    print("=" * 80)

    json_path = output_dir / f"replay_malaysian_snr_2y_metrics.json"
    metrics = {
        "days": days,
        "initial_balance": 10000.0,
        "total_trades": len(all_trades),
        "total_pnl_usd": round(sum(t["total_pnl_usd"] for t in all_trades), 2),
        "active_pnl_usd": round(active_pnl, 2),
        "poda_pnl_usd": round(poda_pnl, 2),
        "active_win_rate": round(active_wr, 1),
        "poda_win_rate": round(poda_wr, 1),
    }
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(metrics, f, indent=2)

    print(f"\nReportes generados en {output_dir}:")
    print(f"  - Trades CSV: {trades_csv.name}")
    print(f"  - Resumen CSV: {sum_csv.name}")
    print(f"  - Métricas JSON: {json_path.name}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Replay Cuantitativo Malaysian SNR 2 Años Multi-Activo")
    parser.add_argument("--days", type=int, default=730, help="Días históricos a analizar (default: 730 = 2 años)")
    args = parser.parse_args()

    run_full_universe_replay(days=args.days)
