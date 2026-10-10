"""Validación Cuantitativa y Comparativa de 2 Años:
Baseline (Actual en Proyecto) vs Augmented (Malaysian SNR con Mejoras de los 22 Videos).

Objetivo:
Validar empíricamente con datos históricos de MetaTrader 5 (24 meses completos)
si la incorporación de:
1. Rastreo estricto de niveles Fresh (Mitigation Tracker)
2. Filtro de Killzones Institucionales (Londres y Nueva York)
3. Daily Storyline (Alineación D1 -> H1)
4. Quasimodo Estructural (Left Shoulder Retest)
5. Detección de Obstáculos / Key Levels opuestos

produce una mejora comprobable en Win Rate, Factor de Beneficio y PnL
frente a la estrategia actual implementada en el proyecto.
"""

import sys
import os
from pathlib import Path
from datetime import datetime, timezone, timedelta
import json
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
# UNIVERSO REPRESENTATIVO PARA AUDITORÍA COMPARATIVA (24 ACTIVOS CLAVE)
# =====================================================================
UNIVERSE = {
    # 1. FOREX CORE (Donde la versión base tuvo problemas de WR 25-37%)
    "EURUSD": {"category": "FOREX", "base_spread": 0.00014, "is_synth": False},
    "GBPUSD": {"category": "FOREX", "base_spread": 0.00018, "is_synth": False},
    "USDJPY": {"category": "FOREX", "base_spread": 0.015, "is_synth": False},
    "USDCAD": {"category": "FOREX", "base_spread": 0.00018, "is_synth": False},
    "USDCHF": {"category": "FOREX", "base_spread": 0.00016, "is_synth": False},
    "AUDUSD": {"category": "FOREX", "base_spread": 0.00016, "is_synth": False},

    # 2. METALES & COMMODITIES
    "XAUUSD": {"category": "METALS", "base_spread": 0.59, "is_synth": False},
    "XAGUSD": {"category": "METALS", "base_spread": 0.055, "is_synth": False},
    "US Oil": {"category": "COMMODITIES", "base_spread": 0.155, "is_synth": False},

    # 3. CRYPTO & ÍNDICES
    "BTCUSD": {"category": "CRYPTO", "base_spread": 18.5, "is_synth": False},
    "US SP 500": {"category": "INDICES", "base_spread": 0.36, "is_synth": False},
    "US Tech 100": {"category": "INDICES", "base_spread": 0.90, "is_synth": False},
    "Wall Street 30": {"category": "INDICES", "base_spread": 1.80, "is_synth": False},

    # 4. SINTÉTICOS CORE (Para comprobar que no degrade el gran resultado)
    "Step Index": {"category": "SYNTHETICS", "base_spread": 0.10, "is_synth": True},
    "Step Index 200": {"category": "SYNTHETICS", "base_spread": 0.20, "is_synth": True},
    "Jump 10 Index": {"category": "SYNTHETICS", "base_spread": 0.50, "is_synth": True},
    "Jump 25 Index": {"category": "SYNTHETICS", "base_spread": 0.60, "is_synth": True},
    "Jump 50 Index": {"category": "SYNTHETICS", "base_spread": 1.25, "is_synth": True},
    "Volatility 10 Index": {"category": "SYNTHETICS", "base_spread": 0.50, "is_synth": True},
    "Volatility 25 Index": {"category": "SYNTHETICS", "base_spread": 1.20, "is_synth": True},
    "Volatility 75 Index": {"category": "SYNTHETICS", "base_spread": 15.8, "is_synth": True},
    "Boom 1000 Index": {"category": "SYNTHETICS", "base_spread": 1.75, "is_synth": True},
    "Boom 500 Index": {"category": "SYNTHETICS", "base_spread": 1.20, "is_synth": True},
    "Crash 1000 Index": {"category": "SYNTHETICS", "base_spread": 1.75, "is_synth": True},
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

    # Fin de semana
    if (weekday == 4 and t_float >= 21.0) or (weekday == 5) or (weekday == 6 and t_float < 21.0):
        return 4.0
    # Rollover
    if 21.0 <= t_float < 23.0:
        return 3.0
    # Killzones Londres y NY
    if (7.0 <= t_float <= 11.0) or (12.5 <= t_float <= 17.0):
        return 1.0
    return 1.5


def is_market_open(timestamp, is_synthetic: bool = False) -> bool:
    if is_synthetic:
        return True
    ts = pd.to_datetime(timestamp, utc=True)
    weekday = ts.weekday()
    hour = ts.hour + ts.minute / 60.0
    if (weekday == 4 and hour >= 21.0) or (weekday == 5) or (weekday == 6 and hour < 21.0):
        return False
    return True


# =====================================================================
# MOTOR BASELINE: LO QUE ESTÁ ACTUALMENTE IMPLEMENTADO EN EL PROYECTO
# =====================================================================
def detect_baseline_setups(df_h1: pd.DataFrame, df_m15: pd.DataFrame, symbol: str, is_synth: bool) -> list[dict]:
    """Implementa estrictamente la lógica de malaysian_snr_strategy.py actual."""
    df_h1 = df_h1.copy()
    df_h1["atr"] = compute_atr(df_h1, 14)
    df_h1["adx"] = compute_adx(df_h1, 14)

    h1_levels = []
    for i in range(2, len(df_h1) - 1):
        prev = df_h1.iloc[i - 1]
        curr = df_h1.iloc[i]
        if prev["close"] > prev["open"] and curr["close"] < curr["open"]:
            if curr["close"] <= prev["open"]:
                h1_levels.append({
                    "type": "A_RESISTANCE",
                    "level": max(prev["high"], curr["high"]),
                    "break_level": prev["close"],
                    "time": curr["time"],
                    "idx": i,
                })
        elif prev["close"] < prev["open"] and curr["close"] > curr["open"]:
            if curr["close"] >= prev["open"]:
                h1_levels.append({
                    "type": "V_SUPPORT",
                    "level": min(prev["low"], curr["low"]),
                    "break_level": prev["close"],
                    "time": curr["time"],
                    "idx": i,
                })

    setups = []
    h1_len = len(df_h1)

    for k in range(20, h1_len):
        candle = df_h1.iloc[k]
        c_time = candle["time"]
        if not is_market_open(c_time, is_synth):
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
        body_ratio = abs(c_close - c_open) / c_span

        # ESCENARIO 1: Ruptura Clásica (ADX >= 20)
        if c_adx >= 20.0:
            recent_levels = [lvl for lvl in h1_levels if 2 < (k - lvl["idx"]) <= 25]
            for lvl in reversed(recent_levels):
                lvl_price = lvl["level"]
                break_price = lvl["break_level"]

                if lvl["type"] == "A_RESISTANCE":
                    upper_wick = c_high - c_close
                    upper_wick_ratio = upper_wick / c_span
                    if c_close > lvl_price and body_ratio >= 0.50 and upper_wick_ratio <= 0.30:
                        if is_direction_allowed(symbol, "BUY"):
                            sl = c_low - (0.15 * c_atr)
                            risk = abs(c_close - sl)
                            if risk > 0:
                                setups.append({
                                    "symbol": symbol,
                                    "variant": "BASELINE",
                                    "scenario": "ESC_1_CONTINUATION",
                                    "direction": "BUY",
                                    "time": c_time,
                                    "entry_price": c_close,
                                    "stop_loss": sl,
                                    "risk_distance": risk,
                                    "momentum_adx": c_adx,
                                    "body_ratio": body_ratio,
                                    "ref_level": lvl_price,
                                })
                                break

                elif lvl["type"] == "V_SUPPORT":
                    lower_wick = c_close - c_low
                    lower_wick_ratio = lower_wick / c_span
                    if c_close < lvl_price and body_ratio >= 0.50 and lower_wick_ratio <= 0.30:
                        if is_direction_allowed(symbol, "SELL"):
                            sl = c_high + (0.15 * c_atr)
                            risk = abs(sl - c_close)
                            if risk > 0:
                                setups.append({
                                    "symbol": symbol,
                                    "variant": "BASELINE",
                                    "scenario": "ESC_1_CONTINUATION",
                                    "direction": "SELL",
                                    "time": c_time,
                                    "entry_price": c_close,
                                    "stop_loss": sl,
                                    "risk_distance": risk,
                                    "momentum_adx": c_adx,
                                    "body_ratio": body_ratio,
                                    "ref_level": lvl_price,
                                })
                                break

        # ESCENARIO 3: Fractalidad 3 velas
        if k >= 3:
            c_prev2 = df_h1.iloc[k - 2]
            c_prev1 = df_h1.iloc[k - 1]
            c_curr = candle

            if c_prev1["low"] < c_prev2["low"] and c_curr["close"] > c_curr["open"]:
                f_body = c_curr["close"] - c_curr["open"]
                f_span = c_curr["high"] - c_curr["low"]
                neckline = float(c_prev2["high"])
                if f_span > 0 and (f_body / f_span) >= 0.55 and c_curr["close"] > neckline:
                    if is_direction_allowed(symbol, "BUY"):
                        sl = float(c_curr["low"]) - (0.15 * c_atr)
                        risk = abs(c_curr["close"] - sl)
                        if risk > 0:
                            setups.append({
                                "symbol": symbol,
                                "variant": "BASELINE",
                                "scenario": "ESC_3_FRACTAL",
                                "direction": "BUY",
                                "time": c_time,
                                "entry_price": c_curr["close"],
                                "stop_loss": sl,
                                "risk_distance": risk,
                                "momentum_adx": c_adx,
                                "body_ratio": f_body / f_span,
                                "ref_level": neckline,
                            })

            elif c_prev1["high"] > c_prev2["high"] and c_curr["close"] < c_curr["open"]:
                f_body = c_curr["open"] - c_curr["close"]
                f_span = c_curr["high"] - c_curr["low"]
                neckline = float(c_prev2["low"])
                if f_span > 0 and (f_body / f_span) >= 0.55 and c_curr["close"] < neckline:
                    if is_direction_allowed(symbol, "SELL"):
                        sl = float(c_curr["high"]) + (0.15 * c_atr)
                        risk = abs(sl - c_curr["close"])
                        if risk > 0:
                            setups.append({
                                "symbol": symbol,
                                "variant": "BASELINE",
                                "scenario": "ESC_3_FRACTAL",
                                "direction": "SELL",
                                "time": c_time,
                                "entry_price": c_curr["close"],
                                "stop_loss": sl,
                                "risk_distance": risk,
                                "momentum_adx": c_adx,
                                "body_ratio": f_body / f_span,
                                "ref_level": neckline,
                            })

    # Deduplicar señales cercanas
    setups = sorted(setups, key=lambda s: s["time"])
    deduped = []
    last_t = None
    for s in setups:
        if last_t is None or (s["time"] - last_t) >= timedelta(hours=3):
            deduped.append(s)
            last_t = s["time"]
    return deduped


# =====================================================================
# MOTOR AUGMENTED: MALAYSIAN SNR ENRIQUECIDO CON LOS 22 VIDEOS
# =====================================================================
def detect_augmented_setups(
    df_h1: pd.DataFrame,
    df_d1: pd.DataFrame,
    symbol: str,
    is_synth: bool
) -> list[dict]:
    """Incorpora los hallazgos institucionales de Malaysian SNR:
    1. True Fresh Level Tracking (Ninguna vela intermedia tocó el nivel antes del quiebre).
    2. Session Killzones (Londres 07-11 UTC, NY 12:30-17 UTC para activos convencionales).
    3. Daily Storyline (Alineación con la vela D1 previa y su tendencia).
    4. Quasimodo Estructural de Swing (Higher High barre liquidez -> Lower Low quiebra -> Retest Left Shoulder).
    5. Obstacle Awareness (Detección de niveles contrarios).
    """
    df_h1 = df_h1.copy()
    df_h1["atr"] = compute_atr(df_h1, 14)
    df_h1["adx"] = compute_adx(df_h1, 14)

    # 1. Mapa de Storyline Diaria
    df_d1 = df_d1.copy()
    df_d1["d1_bullish"] = df_d1["close"] > df_d1["open"]
    df_d1["d1_body"] = (df_d1["close"] - df_d1["open"]).abs()
    df_d1["d1_span"] = df_d1["high"] - df_d1["low"]
    d1_map = {}
    for _, row in df_d1.iterrows():
        d_date = row["time"].date()
        d1_map[d_date] = {
            "bullish": bool(row["d1_bullish"]),
            "close": float(row["close"]),
            "high": float(row["high"]),
            "low": float(row["low"]),
        }

    # 2. Detección de niveles A y V con tracking de Fresh
    h1_levels = []
    for i in range(2, len(df_h1) - 1):
        prev = df_h1.iloc[i - 1]
        curr = df_h1.iloc[i]
        if prev["close"] > prev["open"] and curr["close"] < curr["open"]:
            if curr["close"] <= prev["open"]:
                h1_levels.append({
                    "type": "A_RESISTANCE",
                    "level": max(prev["high"], curr["high"]),
                    "break_level": prev["close"],
                    "time": curr["time"],
                    "idx": i,
                })
        elif prev["close"] < prev["open"] and curr["close"] > curr["open"]:
            if curr["close"] >= prev["open"]:
                h1_levels.append({
                    "type": "V_SUPPORT",
                    "level": min(prev["low"], curr["low"]),
                    "break_level": prev["close"],
                    "time": curr["time"],
                    "idx": i,
                })

    setups = []
    h1_len = len(df_h1)

    for k in range(25, h1_len):
        candle = df_h1.iloc[k]
        c_time = candle["time"]
        if not is_market_open(c_time, is_synth):
            continue

        # MEJORA 1: FILTRO DE SESIONES INSTITUCIONALES (KILLZONES)
        # MR.R & Néstor: En Forex, Metales y Commodities, operar solo en Londres o New York.
        if not is_synth:
            t_float = c_time.hour + (c_time.minute / 60.0)
            in_london = (7.0 <= t_float <= 11.0)
            in_ny = (12.5 <= t_float <= 17.0)
            if not (in_london or in_ny):
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
        body_ratio = abs(c_close - c_open) / c_span

        # MEJORA 2: DAILY STORYLINE (ALINEACIÓN D1)
        prev_date = (c_time - timedelta(days=1)).date()
        d1_info = d1_map.get(prev_date)
        daily_bullish = d1_info["bullish"] if d1_info else (c_close > c_open)

        # MEJORA 3: TRUE FRESH LEVEL TRACKING (ESCENARIO 1 AUGMENTED)
        recent_levels = [lvl for lvl in h1_levels if 2 < (k - lvl["idx"]) <= 35]

        for lvl in reversed(recent_levels):
            lvl_price = lvl["level"]
            break_price = lvl["break_level"]
            lvl_idx = lvl["idx"]

            # Verificar si el nivel se mantuvo ESTRICTAMENTE FRESH (sin toques intermedios)
            intermediate_df = df_h1.iloc[lvl_idx + 1 : k]
            if lvl["type"] == "A_RESISTANCE":
                was_touched = (intermediate_df["high"] >= lvl_price).any()
                if was_touched:
                    continue  # Nivel Mitigado / Unfresh -> Descartar entrada limpia

                # Ruptura con cuerpo sólido + Storyline Diaria alcista
                upper_wick = c_high - c_close
                upper_wick_ratio = upper_wick / c_span
                if (
                    c_close > lvl_price
                    and body_ratio >= 0.50
                    and upper_wick_ratio <= 0.25
                    and daily_bullish  # Storyline Alignment
                    and c_adx >= 20.0
                ):
                    if is_direction_allowed(symbol, "BUY"):
                        sl = c_low - (0.15 * c_atr)
                        risk = abs(c_close - sl)
                        if risk > 0:
                            # Buscar si hay un obstáculo cercano (Key Level opuesto)
                            opp_lvls = [ol["level"] for ol in recent_levels if ol["type"] == "A_RESISTANCE" and ol["level"] > c_close]
                            nearest_obstacle = min(opp_lvls) if opp_lvls else 0.0

                            setups.append({
                                "symbol": symbol,
                                "variant": "AUGMENTED",
                                "scenario": "ESC_1_FRESH_C_TRADE",
                                "direction": "BUY",
                                "time": c_time,
                                "entry_price": c_close,
                                "stop_loss": sl,
                                "risk_distance": risk,
                                "momentum_adx": c_adx,
                                "body_ratio": body_ratio,
                                "ref_level": lvl_price,
                                "obstacle_level": nearest_obstacle,
                            })
                            break

            elif lvl["type"] == "V_SUPPORT":
                was_touched = (intermediate_df["low"] <= lvl_price).any()
                if was_touched:
                    continue  # Nivel Mitigado / Unfresh -> Descartar entrada limpia

                # Ruptura con cuerpo sólido + Storyline Diaria bajista
                lower_wick = c_close - c_low
                lower_wick_ratio = lower_wick / c_span
                if (
                    c_close < lvl_price
                    and body_ratio >= 0.50
                    and lower_wick_ratio <= 0.25
                    and not daily_bullish  # Storyline Alignment
                    and c_adx >= 20.0
                ):
                    if is_direction_allowed(symbol, "SELL"):
                        sl = c_high + (0.15 * c_atr)
                        risk = abs(sl - c_close)
                        if risk > 0:
                            opp_lvls = [ol["level"] for ol in recent_levels if ol["type"] == "V_SUPPORT" and ol["level"] < c_close]
                            nearest_obstacle = max(opp_lvls) if opp_lvls else 0.0

                            setups.append({
                                "symbol": symbol,
                                "variant": "AUGMENTED",
                                "scenario": "ESC_1_FRESH_C_TRADE",
                                "direction": "SELL",
                                "time": c_time,
                                "entry_price": c_close,
                                "stop_loss": sl,
                                "risk_distance": risk,
                                "momentum_adx": c_adx,
                                "body_ratio": body_ratio,
                                "ref_level": lvl_price,
                                "obstacle_level": nearest_obstacle,
                            })
                            break

        # MEJORA 4: QUASIMODO (QM) ESTRUCTURAL
        # High -> Low -> Higher High (barrido) -> Lower Low (quiebre) -> Retest Left Shoulder
        if k >= 6:
            c1 = df_h1.iloc[k - 4]
            c2 = df_h1.iloc[k - 3]
            c3 = df_h1.iloc[k - 2]
            c4 = df_h1.iloc[k - 1]
            c5 = candle

            # Bullish QM: Low (c1) -> High (c2) -> Lower Low sweep (c3) -> Higher High break (c4) -> Retest (c5)
            if (
                c3["low"] < c1["low"]  # Barrido de liquidez de mínimos
                and c4["close"] > c2["high"]  # Quiebre de estructura al alza
                and c5["low"] <= c1["low"] + (0.25 * c_atr)  # Retest al Left Shoulder (c1["low"])
                and c5["close"] > c1["low"]
            ):
                if is_direction_allowed(symbol, "BUY") and daily_bullish:
                    sl = c3["low"] - (0.10 * c_atr)
                    risk = abs(c5["close"] - sl)
                    if risk > 0:
                        setups.append({
                            "symbol": symbol,
                            "variant": "AUGMENTED",
                            "scenario": "ESC_3_QUASIMODO",
                            "direction": "BUY",
                            "time": c_time,
                            "entry_price": c5["close"],
                            "stop_loss": sl,
                            "risk_distance": risk,
                            "momentum_adx": c_adx,
                            "body_ratio": body_ratio,
                            "ref_level": c1["low"],
                            "obstacle_level": c2["high"],
                        })

            # Bearish QM: High (c1) -> Low (c2) -> Higher High sweep (c3) -> Lower Low break (c4) -> Retest (c5)
            elif (
                c3["high"] > c1["high"]  # Barrido de liquidez de máximos
                and c4["close"] < c2["low"]  # Quiebre de estructura a la baja
                and c5["high"] >= c1["high"] - (0.25 * c_atr)  # Retest al Left Shoulder (c1["high"])
                and c5["close"] < c1["high"]
            ):
                if is_direction_allowed(symbol, "SELL") and not daily_bullish:
                    sl = c3["high"] + (0.10 * c_atr)
                    risk = abs(sl - c5["close"])
                    if risk > 0:
                        setups.append({
                            "symbol": symbol,
                            "variant": "AUGMENTED",
                            "scenario": "ESC_3_QUASIMODO",
                            "direction": "SELL",
                            "time": c_time,
                            "entry_price": c5["close"],
                            "stop_loss": sl,
                            "risk_distance": risk,
                            "momentum_adx": c_adx,
                            "body_ratio": body_ratio,
                            "ref_level": c1["high"],
                            "obstacle_level": c2["low"],
                        })

    # Deduplicar señales cercanas (mínimo 3 horas)
    setups = sorted(setups, key=lambda s: s["time"])
    deduped = []
    last_t = None
    for s in setups:
        if last_t is None or (s["time"] - last_t) >= timedelta(hours=3):
            deduped.append(s)
            last_t = s["time"]
    return deduped


# =====================================================================
# SIMULADOR NUMPY DUAL-LEG DE 2 AÑOS (IDÉNTICO PARA AMBAS VARIANTES)
# =====================================================================
def simulate_dual_leg(
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
    variant = setup["variant"]
    adx = float(setup.get("momentum_adx", 20.0))
    body_ratio = float(setup.get("body_ratio", 0.6))
    risk_dist = float(setup["risk_distance"])
    obstacle_level = float(setup.get("obstacle_level", 0.0))

    if risk_dist <= 0:
        return None

    target_dt64 = np.datetime64(entry_time)
    start_idx = np.searchsorted(m15_times_np, target_dt64)
    n_bars = len(m15_times_np)
    if start_idx >= n_bars - 3:
        return None

    end_idx = min(n_bars, start_idx + max_hold_bars)

    # TP1: 1:2.0 RR (Dual-Leg)
    tp1_rr = 2.0
    tp1_price = entry_price + (2.0 * risk_dist) if direction == "BUY" else entry_price - (2.0 * risk_dist)

    # Asignación de la corredora TP2
    if adx >= 28.0 and body_ratio >= 0.65:
        tp2_rr = 4.0
    elif adx >= 22.0:
        tp2_rr = 3.0
    else:
        tp2_rr = 2.5

    # Si hay un obstáculo estructural previo en la variante Augmented, ajustar TP2
    if variant == "AUGMENTED" and obstacle_level > 0:
        dist_to_obs = abs(obstacle_level - entry_price) / risk_dist
        if 1.8 < dist_to_obs < tp2_rr:
            tp2_rr = round(dist_to_obs - 0.2, 1)

    tp2_price = entry_price + (tp2_rr * risk_dist) if direction == "BUY" else entry_price - (tp2_rr * risk_dist)

    risk_usd_leg = 50.0  # 0.5% en cada pierna sobre $10k
    be_buffer = base_spread * 1.5
    be_price = entry_price + be_buffer if direction == "BUY" else entry_price - be_buffer

    leg1_closed = False
    leg1_pnl_usd = 0.0
    leg1_rr = 0.0

    leg2_closed = False
    leg2_pnl_usd = 0.0
    leg2_rr = 0.0
    leg2_in_be = False

    sub_highs = m15_highs[start_idx:end_idx]
    sub_lows = m15_lows[start_idx:end_idx]
    sub_closes = m15_closes[start_idx:end_idx]
    sub_times = m15_times_np[start_idx:end_idx]

    for bar_i in range(len(sub_highs)):
        high = sub_highs[bar_i]
        low = sub_lows[bar_i]
        close = sub_closes[bar_i]
        c_time = sub_times[bar_i]

        spread_mult = get_spread_multiplier(c_time, is_synthetic)
        eff_spread = base_spread * spread_mult

        if direction == "BUY":
            hit_sl = low <= (stop_loss + eff_spread)
            hit_tp1 = high >= tp1_price
            hit_tp2 = high >= tp2_price
        else:
            hit_sl = high >= (stop_loss - eff_spread)
            hit_tp1 = low <= tp1_price
            hit_tp2 = low <= tp2_price

        # Pierna 1
        if not leg1_closed:
            if hit_sl and hit_tp1:
                hit_sl, hit_tp1 = True, False

            if hit_sl:
                leg1_closed = True
                leg1_rr = -1.0
                leg1_pnl_usd = -risk_usd_leg

                leg2_closed = True
                leg2_rr = -1.0
                leg2_pnl_usd = -risk_usd_leg
                break

            elif hit_tp1:
                leg1_closed = True
                leg1_rr = tp1_rr
                leg1_pnl_usd = risk_usd_leg * tp1_rr
                leg2_in_be = True

        # Pierna 2
        if leg1_closed and not leg2_closed:
            curr_sl = be_price if leg2_in_be else stop_loss
            be_sl_hit = (low <= curr_sl) if direction == "BUY" else (high >= curr_sl)

            if hit_tp2:
                leg2_closed = True
                leg2_rr = tp2_rr
                leg2_pnl_usd = risk_usd_leg * tp2_rr
                break
            elif be_sl_hit:
                leg2_closed = True
                leg2_rr = 0.0
                leg2_pnl_usd = 0.0
                break

    if not leg1_closed:
        pnl_diff = (close - entry_price) if direction == "BUY" else (entry_price - close)
        leg1_rr = max(-1.0, min(tp1_rr, pnl_diff / risk_dist))
        leg1_pnl_usd = risk_usd_leg * leg1_rr

    if not leg2_closed:
        pnl_diff = (close - entry_price) if direction == "BUY" else (entry_price - close)
        leg2_rr = max(0.0 if leg2_in_be else -1.0, min(tp2_rr, pnl_diff / risk_dist))
        leg2_pnl_usd = risk_usd_leg * leg2_rr

    total_pnl_usd = leg1_pnl_usd + leg2_pnl_usd
    total_rr = (leg1_rr * 0.5) + (leg2_rr * 0.5)
    trade_result = "WIN" if total_pnl_usd > 0 else ("BE" if total_pnl_usd == 0 else "LOSS")

    return {
        "symbol": symbol,
        "variant": variant,
        "scenario": scenario,
        "direction": direction,
        "entry_time": str(entry_time),
        "entry_price": entry_price,
        "stop_loss": stop_loss,
        "risk_distance": risk_dist,
        "total_pnl_usd": total_pnl_usd,
        "total_rr": round(total_rr, 3),
        "trade_result": trade_result,
    }


# =====================================================================
# EJECUTOR PRINCIPAL DE COMPARACIÓN HEAD-TO-HEAD
# =====================================================================
def run_comparison(days: int = 730):
    print("=" * 115)
    print(f"AUDITORÍA CIENTÍFICA COMPARATIVA: MALAYSIAN SNR BASELINE vs AUGMENTED ({days} DÍAS - 2 AÑOS)")
    print("Variante A (BASELINE) : Implementación actual en el bot (H1/M15, ADX, sin Killzones, sin D1)")
    print("Variante B (AUGMENTED): Mejoras de los 22 videos (True Fresh, Session Killzones, Daily Storyline, QM)")
    print("=" * 115)

    if not mt5.initialize():
        print("[ERROR] MetaTrader 5 no está disponible.")
        return

    now = datetime.now(timezone.utc)
    start_time = now - timedelta(days=days)

    results_baseline = []
    results_augmented = []
    asset_comparison = []

    t0 = time.time()

    for idx, (sym, meta) in enumerate(UNIVERSE.items(), start=1):
        cat = meta["category"]
        base_spread = meta["base_spread"]
        is_synth = meta["is_synth"]

        print(f"[{idx:02d}/{len(UNIVERSE)}] Evaluando {sym:<20} ({cat:<11})...", end=" ", flush=True)

        mt5.symbol_select(sym, True)
        rates_d1 = mt5.copy_rates_range(sym, mt5.TIMEFRAME_D1, start_time - timedelta(days=30), now)
        rates_h1 = mt5.copy_rates_range(sym, mt5.TIMEFRAME_H1, start_time, now)
        rates_m15 = mt5.copy_rates_range(sym, mt5.TIMEFRAME_M15, start_time, now)

        if rates_h1 is None or len(rates_h1) < 100 or rates_m15 is None or len(rates_m15) < 500:
            print("DATOS INSUFICIENTES (Omitido)")
            continue

        df_d1 = pd.DataFrame(rates_d1)
        df_d1["time"] = pd.to_datetime(df_d1["time"], unit="s", utc=True)

        df_h1 = pd.DataFrame(rates_h1)
        df_h1["time"] = pd.to_datetime(df_h1["time"], unit="s", utc=True)

        df_m15 = pd.DataFrame(rates_m15)
        df_m15["time"] = pd.to_datetime(df_m15["time"], unit="s", utc=True)

        m15_times_np = df_m15["time"].values.astype("datetime64[ns]")
        m15_highs = df_m15["high"].values.astype(float)
        m15_lows = df_m15["low"].values.astype(float)
        m15_closes = df_m15["close"].values.astype(float)

        # 1. Ejecutar Baseline
        setups_a = detect_baseline_setups(df_h1, df_m15, sym, is_synth)
        trades_a = []
        for s in setups_a:
            res = simulate_dual_leg(s, m15_times_np, m15_highs, m15_lows, m15_closes, base_spread, is_synth)
            if res:
                res["category"] = cat
                trades_a.append(res)
                results_baseline.append(res)

        # 2. Ejecutar Augmented
        setups_b = detect_augmented_setups(df_h1, df_d1, sym, is_synth)
        trades_b = []
        for s in setups_b:
            res = simulate_dual_leg(s, m15_times_np, m15_highs, m15_lows, m15_closes, base_spread, is_synth)
            if res:
                res["category"] = cat
                trades_b.append(res)
                results_augmented.append(res)

        # Métricas individuales por activo
        n_a = len(trades_a)
        wr_a = (sum(1 for t in trades_a if t["trade_result"] == "WIN") / n_a * 100.0) if n_a > 0 else 0.0
        pnl_a = sum(t["total_pnl_usd"] for t in trades_a)

        n_b = len(trades_b)
        wr_b = (sum(1 for t in trades_b if t["trade_result"] == "WIN") / n_b * 100.0) if n_b > 0 else 0.0
        pnl_b = sum(t["total_pnl_usd"] for t in trades_b)

        wr_diff = wr_b - wr_a
        pnl_diff = pnl_b - pnl_a

        asset_comparison.append({
            "symbol": sym,
            "category": cat,
            "trades_baseline": n_a,
            "wr_baseline": round(wr_a, 1),
            "pnl_baseline": round(pnl_a, 2),
            "trades_augmented": n_b,
            "wr_augmented": round(wr_b, 1),
            "pnl_augmented": round(pnl_b, 2),
            "wr_diff": round(wr_diff, 1),
            "pnl_diff": round(pnl_diff, 2),
        })

        print(f"Base: {n_a:3d} trd (WR: {wr_a:4.1f}%, ${pnl_a:+8.1f}) | Augm: {n_b:3d} trd (WR: {wr_b:4.1f}%, ${pnl_b:+8.1f}) -> Diff WR: {wr_diff:+4.1f}%")

    mt5.shutdown()
    elapsed = time.time() - t0

    # =====================================================================
    # CONSOLIDACIÓN Y RESUMEN COMPARATIVO
    # =====================================================================
    df_cmp = pd.DataFrame(asset_comparison)
    output_dir = PROJECT_ROOT / "storage" / "analysis"
    output_dir.mkdir(parents=True, exist_ok=True)
    df_cmp.to_csv(output_dir / "comparison_malaysian_snr_baseline_vs_augmented.csv", index=False)

    total_a_trades = len(results_baseline)
    wins_a = sum(1 for t in results_baseline if t["trade_result"] == "WIN")
    losses_a = sum(1 for t in results_baseline if t["trade_result"] == "LOSS")
    wr_a_tot = (wins_a / total_a_trades * 100.0) if total_a_trades > 0 else 0.0
    pnl_a_tot = sum(t["total_pnl_usd"] for t in results_baseline)
    profit_a = sum(t["total_pnl_usd"] for t in results_baseline if t["total_pnl_usd"] > 0)
    loss_a_val = abs(sum(t["total_pnl_usd"] for t in results_baseline if t["total_pnl_usd"] < 0))
    pf_a = (profit_a / loss_a_val) if loss_a_val > 0 else 999.0

    total_b_trades = len(results_augmented)
    wins_b = sum(1 for t in results_augmented if t["trade_result"] == "WIN")
    losses_b = sum(1 for t in results_augmented if t["trade_result"] == "LOSS")
    wr_b_tot = (wins_b / total_b_trades * 100.0) if total_b_trades > 0 else 0.0
    pnl_b_tot = sum(t["total_pnl_usd"] for t in results_augmented)
    profit_b = sum(t["total_pnl_usd"] for t in results_augmented if t["total_pnl_usd"] > 0)
    loss_b_val = abs(sum(t["total_pnl_usd"] for t in results_augmented if t["total_pnl_usd"] < 0))
    pf_b = (profit_b / loss_b_val) if loss_b_val > 0 else 999.0

    print("\n" + "=" * 115)
    print("RESUMEN GLOBAL DE LA AUDITORÍA DE 2 AÑOS (BASELINE vs AUGMENTED)")
    print("=" * 115)
    print(f"{'MÉTRICA GLOBAL':<30} | {'BASELINE (ACTUAL)':<22} | {'AUGMENTED (VIDEOS)':<22} | {'DIFERENCIA / DELTA'}")
    print("-" * 115)
    print(f"{'Total Operaciones':<30} | {total_a_trades:<22d} | {total_b_trades:<22d} | {total_b_trades - total_a_trades:+d} trades")
    print(f"{'Win Rate Global (%)':<30} | {wr_a_tot:>20.2f}% | {wr_b_tot:>20.2f}% | {wr_b_tot - wr_a_tot:>+18.2f}%")
    print(f"{'PnL Neto Total (USD)':<30} | ${pnl_a_tot:>19.2f} | ${pnl_b_tot:>19.2f} | ${pnl_b_tot - pnl_a_tot:>+17.2f}")
    print(f"{'Factor de Beneficio (PF)':<30} | {pf_a:>21.2f} | {pf_b:>21.2f} | {pf_b - pf_a:>+19.2f}")
    print("=" * 115)

    # Desglose por categoría
    print("\n" + "=" * 115)
    print("DESGLOSE POR CATEGORÍA DE ACTIVO (WIN RATE COMPARATIVO)")
    print("=" * 115)
    print(f"{'CATEGORÍA':<15} | {'TRD BASE':<10} | {'WR BASE (%)':<12} | {'TRD AUGM':<10} | {'WR AUGM (%)':<12} | {'DELTA WR (%)':<14} | {'DELTA PNL (USD)'}")
    print("-" * 115)
    for cat in ["FOREX", "METALS", "COMMODITIES", "CRYPTO", "INDICES", "SYNTHETICS"]:
        sub_cmp = df_cmp[df_cmp["category"] == cat]
        if sub_cmp.empty:
            continue
        c_trd_a = sub_cmp["trades_baseline"].sum()
        c_pnl_a = sub_cmp["pnl_baseline"].sum()
        c_wr_a = (sub_cmp["trades_baseline"] * sub_cmp["wr_baseline"]).sum() / c_trd_a if c_trd_a > 0 else 0.0

        c_trd_b = sub_cmp["trades_augmented"].sum()
        c_pnl_b = sub_cmp["pnl_augmented"].sum()
        c_wr_b = (sub_cmp["trades_augmented"] * sub_cmp["wr_augmented"]).sum() / c_trd_b if c_trd_b > 0 else 0.0

        print(f"{cat:<15} | {c_trd_a:<10d} | {c_wr_a:>10.1f}% | {c_trd_b:<10d} | {c_wr_b:>10.1f}% | {c_wr_b - c_wr_a:>+12.1f}% | ${c_pnl_b - c_pnl_a:>+14.2f}")
    print("=" * 115)

    # Guardar métricas JSON
    summary_json = {
        "days": days,
        "elapsed_seconds": round(elapsed, 1),
        "baseline": {
            "trades": total_a_trades,
            "win_rate": round(wr_a_tot, 2),
            "net_pnl": round(pnl_a_tot, 2),
            "profit_factor": round(pf_a, 2),
        },
        "augmented": {
            "trades": total_b_trades,
            "win_rate": round(wr_b_tot, 2),
            "net_pnl": round(pnl_b_tot, 2),
            "profit_factor": round(pf_b, 2),
        },
        "delta": {
            "win_rate": round(wr_b_tot - wr_a_tot, 2),
            "pnl": round(pnl_b_tot - pnl_a_tot, 2),
            "profit_factor": round(pf_b - pf_a, 2),
        }
    }
    with open(output_dir / "comparison_malaysian_snr_metrics.json", "w", encoding="utf-8") as f:
        json.dump(summary_json, f, indent=2)

    print(f"\nResultados guardados exitosamente en:\n  - {output_dir / 'comparison_malaysian_snr_baseline_vs_augmented.csv'}\n  - {output_dir / 'comparison_malaysian_snr_metrics.json'}")


if __name__ == "__main__":
    run_comparison(days=730)
