"""Auditoría y Replay Comparativo de 2 Años: Estrategia ICT Sabri Malle (60 Activos)
================================================================================
Compara:
1. Baseline ICT (Versión previa: Solo Londres en reales, entrada a mercado inmediata al cierre del MSS,
   sintéticos con rangos rígidos, sin guardias de rollover/fin de semana).
2. Augmented ICT v2.1 (Versión optimizada: Killzones Londres + NY con guardias de fin de semana
   y rollover, Sintéticos 24/7 continuos con ciclos dinámicos de volatilidad,
   Entrada en Consequent Encroachment al 50% del FVG / retesteo, política Boom/Crash).

Universo: 60 Activos (Forex Core & Poda, Metales, Cripto, Commodities, Índices,
Sintéticos Boom, Crash, Step, Jump, Volatility).
"""
from __future__ import annotations

import argparse
import json
import math
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Codificación UTF-8 en consola Windows
for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

from config.symbol_policy import is_direction_allowed
from tools.replay_malaysian_snr_full_universe import ASSET_UNIVERSE

NEW_YORK = ZoneInfo("America/New_York")
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


def build_h4_candles_from_h1(df_h1: pd.DataFrame) -> pd.DataFrame:
    df = df_h1.copy()
    h4 = df.set_index("time").resample("4h", label="left", closed="left").agg({
        "open": "first",
        "high": "max",
        "low": "min",
        "close": "last",
        "tick_volume": "sum",
    }).dropna().reset_index()
    h4["time"] = pd.to_datetime(h4["time"], utc=True)
    return h4


def load_dataset(symbol: str) -> dict[str, pd.DataFrame] | None:
    prefix = symbol.replace(" ", "_")
    cache_dir = PROJECT_ROOT / "data" / "cache_msnr"
    h1_pkl = cache_dir / f"{prefix}_H1.pkl"
    m15_pkl = cache_dir / f"{prefix}_M15.pkl"

    if not (h1_pkl.exists() and m15_pkl.exists()):
        return None

    df_h1 = pd.read_pickle(h1_pkl)
    df_m15 = pd.read_pickle(m15_pkl)
    df_h1["time"] = pd.to_datetime(df_h1["time"], utc=True)
    df_h1 = df_h1.sort_values("time").drop_duplicates("time").reset_index(drop=True)
    df_m15["time"] = pd.to_datetime(df_m15["time"], utc=True)
    df_m15 = df_m15.sort_values("time").drop_duplicates("time").reset_index(drop=True)

    df_h4 = build_h4_candles_from_h1(df_h1)

    return {"H1": df_h1, "M15": df_m15, "H4": df_h4}


def to_utc_timestamp(dt: Any) -> pd.Timestamp:
    ts = pd.Timestamp(dt)
    if ts.tzinfo is None:
        return ts.tz_localize("UTC")
    return ts.tz_convert("UTC")


def is_market_closed_or_rollover(dt_raw: Any, is_synth: bool) -> bool:
    """Para mercados reales (no sintéticos), verifica cierres de fin de semana y ventana rollover."""
    if is_synth:
        return False  # Sintéticos operan 24/7 sin cierres
    dt_utc = to_utc_timestamp(dt_raw)
    dt_ny = dt_utc.tz_convert(NEW_YORK)
    weekday = dt_ny.weekday()  # 0=Lunes, 4=Viernes, 5=Sábado, 6=Domingo
    hour = dt_ny.hour
    minute = dt_ny.minute

    # Fin de semana:
    # Viernes después de las 14:00 NY -> Bloqueo para evitar rollover de fin de semana
    if weekday == 4 and hour >= 14:
        return True
    # Sábado completo
    if weekday == 5:
        return True
    # Domingo antes de las 17:00 NY (Apertura de Sydney/Tokyo)
    if weekday == 6 and hour < 17:
        return True

    # Guardia de Rollover diario bancario (16:45 a 17:45 NY): Spreads se multiplican 5x-10x
    if (hour == 16 and minute >= 45) or (hour == 17 and minute <= 45):
        return True

    return False


def is_killzone_active(dt_raw: Any, is_synth: bool, mode: str, cat: str = "") -> bool:
    """Verifica si la sesión actual está activa."""
    if is_synth:
        return True  # Sintéticos operan 24/7
    dt_utc = to_utc_timestamp(dt_raw)
    dt_ny = dt_utc.tz_convert(NEW_YORK)
    h = dt_ny.hour
    # London Killzone: 02:00 a 05:00 NY
    in_london = (2 <= h <= 5)
    # New York Killzone: 07:00 a 11:00 NY
    in_ny = (7 <= h <= 11)

    if mode == "baseline":
        # Baseline anterior solo operaba Londres
        return in_london
    else:
        # Augmented: En Forex la Killzone institucional de alta probabilidad es Londres (02:00-05:00 NY).
        # En Metales, Índices, Commodities y Cripto se operan Londres y Nueva York.
        if "FOREX" in cat:
            return in_london
        return in_london or in_ny




def find_active_fvgs_fast(h4_df: pd.DataFrame, h4_idx: int, lookback_bars: int = 40) -> list[dict]:
    if h4_idx < 4:
        return []
    start_idx = max(2, h4_idx - lookback_bars)
    fvgs = []
    highs = h4_df["high"].values
    lows = h4_df["low"].values
    closes = h4_df["close"].values
    opens = h4_df["open"].values

    for i in range(start_idx, h4_idx + 1):
        if lows[i - 2] > highs[i] and closes[i - 1] < opens[i - 1]:
            gap_top = float(lows[i - 2])
            gap_bottom = float(highs[i])
            mitigated = False
            for k in range(i + 1, h4_idx + 1):
                if highs[k] >= gap_top:
                    mitigated = True
                    break
            if not mitigated:
                fvgs.append({
                    "type": "BEARISH",
                    "top": gap_top,
                    "bottom": gap_bottom,
                    "midpoint": (gap_top + gap_bottom) / 2.0,
                    "height": gap_top - gap_bottom,
                })
        elif highs[i - 2] < lows[i] and closes[i - 1] > opens[i - 1]:
            gap_top = float(highs[i - 2])
            gap_bottom = float(lows[i])
            mitigated = False
            for k in range(i + 1, h4_idx + 1):
                if lows[k] <= gap_bottom:
                    mitigated = True
                    break
            if not mitigated:
                fvgs.append({
                    "type": "BULLISH",
                    "top": gap_top,
                    "bottom": gap_bottom,
                    "midpoint": (gap_top + gap_bottom) / 2.0,
                    "height": gap_bottom - gap_top,
                })
    return fvgs


def simulate_trade_dual_leg(
    direction: str,
    fill_price: float,
    stop_loss: float,
    tp1_price: float,
    tp2_price: float,
    m15_highs: np.ndarray,
    m15_lows: np.ndarray,
    m15_opens: np.ndarray,
    m15_closes: np.ndarray,
    start_bar: int,
    spread: float,
    max_hold_bars: int = 300,
) -> tuple[float, str, int, bool, bool, bool]:
    """Simulación asimétrica dual fiel (Leg 1 50% @ 2R, Leg 2 50% @ 3.5R con BE automático al tocar TP1).
    Devuelve: (r_neto, outcome, bars_duracion, hit_tp1, hit_tp2, hit_be)
    """
    n = min(len(m15_highs), start_bar + max_hold_bars)
    be_price = fill_price + spread if direction == "BUY" else fill_price - spread

    leg1_closed = False
    leg1_r = 0.0
    leg2_closed = False
    leg2_r = 0.0
    leg2_in_be = False
    hit_tp1 = False
    hit_tp2 = False
    hit_be = False
    bars = 0

    for k in range(start_bar, n):
        bars = k - start_bar + 1
        b_high = m15_highs[k]
        b_low = m15_lows[k]
        b_open = m15_opens[k]

        # 1. Monitoreo previo a TP1
        if not leg1_closed:
            sl_hit = (b_low <= stop_loss) if direction == "BUY" else (b_high >= stop_loss)
            tp1_hit = (b_high >= tp1_price) if direction == "BUY" else (b_low <= tp1_price)

            if sl_hit and tp1_hit:
                # Si ambos se tocan en la misma vela, gana el peor caso (SL) si la apertura fue contraria
                if (direction == "BUY" and b_open < fill_price) or (direction == "SELL" and b_open > fill_price):
                    sl_hit, tp1_hit = True, False
                else:
                    sl_hit, tp1_hit = False, True

            if sl_hit:
                leg1_closed = True
                leg1_r = -1.0 * 0.5  # -0.5R
                leg2_closed = True
                leg2_r = -1.0 * 0.5  # -0.5R
                return (-1.0, "SL_FULL", bars, False, False, False)

            elif tp1_hit:
                leg1_closed = True
                leg1_r = 2.0 * 0.5  # +1.0R asegurado
                hit_tp1 = True
                leg2_in_be = True

        # 2. Monitoreo de Leg 2 tras TP1
        if leg1_closed and not leg2_closed:
            current_sl_leg2 = be_price if leg2_in_be else stop_loss
            be_sl_hit = (b_low <= current_sl_leg2) if direction == "BUY" else (b_high >= current_sl_leg2)
            tp2_hit = (b_high >= tp2_price) if direction == "BUY" else (b_low <= tp2_price)

            if be_sl_hit and tp2_hit:
                if (direction == "BUY" and b_open > current_sl_leg2) or (direction == "SELL" and b_open < current_sl_leg2):
                    tp2_hit, be_sl_hit = True, False
                else:
                    tp2_hit, be_sl_hit = False, True

            if tp2_hit:
                leg2_closed = True
                leg2_r = 3.5 * 0.5  # +1.75R
                hit_tp2 = True
                total_r = leg1_r + leg2_r  # +1.0R + +1.75R = +2.75R
                return (total_r, "TP_FULL", bars, True, True, False)

            elif be_sl_hit:
                leg2_closed = True
                leg2_r = 0.0  # Break Even protegido
                hit_be = True
                total_r = leg1_r + leg2_r  # +1.0R + 0.0R = +1.0R
                return (total_r, "TP1_THEN_BE", bars, True, False, True)

    # Si expira por timeout
    if not leg1_closed:
        return (-1.0, "TIMEOUT_SL", bars, False, False, False)
    else:
        return (leg1_r, "TP1_TIMEOUT", bars, True, False, False)


def run_ict_replay_for_symbol(
    symbol: str,
    frames: dict[str, pd.DataFrame],
    mode: str = "augmented",
) -> list[dict]:
    """Ejecuta el replay bar-a-bar sin lookahead para un símbolo."""
    df_h1 = frames["H1"]
    df_m15 = frames["M15"]
    df_h4 = frames["H4"]

    is_synth = IS_SYNTH_MAP.get(symbol, False)
    spread = SPREADS.get(symbol, 0.00015)
    category = ASSET_CATEGORIES.get(symbol, "OTHER")

    # EMAs en H4
    df_h4 = df_h4.copy()
    df_h4["ema50"] = df_h4["close"].ewm(span=50, adjust=False).mean()
    df_h4["ema200"] = df_h4["close"].ewm(span=200, adjust=False).mean()

    # Pre-calcular ATR en H1
    atr_h1_series = compute_atr(df_h1, period=14).bfill().values

    h1_times = df_h1["time"].values
    h1_highs = df_h1["high"].values
    h1_lows = df_h1["low"].values
    h1_opens = df_h1["open"].values
    h1_closes = df_h1["close"].values

    m15_times = df_m15["time"].values
    m15_highs = df_m15["high"].values
    m15_lows = df_m15["low"].values
    m15_opens = df_m15["open"].values
    m15_closes = df_m15["close"].values

    h4_times = df_h4["time"].values
    h4_closes = df_h4["close"].values
    h4_ema50 = df_h4["ema50"].values
    h4_ema200 = df_h4["ema200"].values

    trades = []
    busy_until_m15 = -1
    n_h1 = len(df_h1)

    i = max(30, 20)
    while i < n_h1 - 10:
        c_time_h1 = to_utc_timestamp(h1_times[i])

        # 1. Filtro de Cierre de Mercado y Rollover (solo para reales)
        if mode == "augmented":
            if is_market_closed_or_rollover(c_time_h1, is_synth):
                i += 1
                continue

        # 2. Filtro de Killzones Institucionales
        if not is_killzone_active(c_time_h1, is_synth, mode, cat=category):
            i += 1
            continue

        # 3. Macro Bias H4 sin lookahead (usar solo velas H4 completamente cerradas)
        h4_idx = int(np.searchsorted(h4_times, np.datetime64(c_time_h1.tz_convert("UTC").tz_localize(None)), side="right")) - 1
        if h4_idx < 15:
            i += 1
            continue

        c_h4_close = h4_closes[h4_idx]
        c_h4_ema50 = h4_ema50[h4_idx]
        c_h4_ema200 = h4_ema200[h4_idx]

        # Alineación institucional estricta H4 (EMAs 50 y 200 en orden de tendencia)
        bias_bearish = (c_h4_close < c_h4_ema50) and (c_h4_ema50 <= c_h4_ema200)
        bias_bullish = (c_h4_close > c_h4_ema50) and (c_h4_ema50 >= c_h4_ema200)

        if not (bias_bearish or bias_bullish):
            i += 1
            continue

        intended_direction = "SELL" if bias_bearish else "BUY"

        # Política de dirección institucional (Boom = BUY, Crash = SELL)
        if not is_direction_allowed(symbol, intended_direction):
            i += 1
            continue


        # 4. Acumulación (A): Rango Asiático (20:00 - 00:00 NY) o Consolidación Previa
        curr_atr = float(atr_h1_series[i])
        if curr_atr <= 0:
            i += 1
            continue

        range_high = None
        range_low = None

        if not is_synth and mode == "augmented":
            dt_ny = c_time_h1.tz_convert(NEW_YORK)
            h_ny = dt_ny.hour
            if 2 <= h_ny <= 5:
                # London KZ barre el Rango Asiático (20:00 a 00:00 NY)
                asian_highs, asian_lows = [], []
                for back in range(1, min(24, i)):
                    bar_t = to_utc_timestamp(h1_times[i - back]).tz_convert(NEW_YORK)
                    if bar_t.hour >= 20 or bar_t.hour <= 0:
                        asian_highs.append(h1_highs[i - back])
                        asian_lows.append(h1_lows[i - back])
                    elif len(asian_highs) > 0:
                        break
                if len(asian_highs) >= 2:
                    range_high = float(np.max(asian_highs))
                    range_low = float(np.min(asian_lows))
            elif 7 <= h_ny <= 11:
                # New York KZ barre el Rango de Londres (02:00 a 05:00 NY)
                london_highs, london_lows = [], []
                for back in range(1, min(16, i)):
                    bar_t = to_utc_timestamp(h1_times[i - back]).tz_convert(NEW_YORK)
                    if 2 <= bar_t.hour <= 5:
                        london_highs.append(h1_highs[i - back])
                        london_lows.append(h1_lows[i - back])
                    elif len(london_highs) > 0:
                        break
                if len(london_highs) >= 2:
                    range_high = float(np.max(london_highs))
                    range_low = float(np.min(london_lows))



        if range_high is None or range_low is None:
            # Consolidación previa (lookback de 20 a 24 barras)
            lb = 24 if mode == "baseline" else 20
            start_lb = max(0, i - lb - 4)
            end_lb = max(0, i - 4)
            if end_lb - start_lb < 8:
                i += 1
                continue
            range_high = float(np.max(h1_highs[start_lb:end_lb]))
            range_low = float(np.min(h1_lows[start_lb:end_lb]))

        range_height = range_high - range_low
        min_factor = 0.5 if mode == "baseline" else 0.45
        max_factor = 5.0

        if range_height < (min_factor * curr_atr) or range_height > (max_factor * curr_atr):
            i += 1
            continue

        # 5. Manipulación (M - Judas Swing): Barrido en las últimas 4 velas H1
        manipulation_found = False
        sweep_peak = None
        sweep_idx = None
        fvgs = find_active_fvgs_fast(df_h4, h4_idx, lookback_bars=40)
        min_wick = 0.35

        for m_idx in range(max(0, i - 4), i + 1):
            c_high = h1_highs[m_idx]
            c_low = h1_lows[m_idx]
            c_open = h1_opens[m_idx]
            c_close = h1_closes[m_idx]
            c_range = c_high - c_low + 1e-9

            if bias_bearish and c_high > range_high:
                fvg_mitigated = any(
                    f["type"] == "BEARISH" and c_high >= f["bottom"] and c_high <= (f["top"] + 0.1 * f["height"])
                    for f in fvgs
                )
                upper_wick = (c_high - max(c_open, c_close)) / c_range
                if fvg_mitigated or (upper_wick >= min_wick):
                    manipulation_found = True
                    sweep_peak = c_high
                    sweep_idx = m_idx
                    break

            elif bias_bullish and c_low < range_low:
                fvg_mitigated = any(
                    f["type"] == "BULLISH" and c_low <= f["top"] and c_low >= (f["bottom"] - 0.1 * f["height"])
                    for f in fvgs
                )
                lower_wick = (min(c_open, c_close) - c_low) / c_range
                if fvg_mitigated or (lower_wick >= min_wick):
                    manipulation_found = True
                    sweep_peak = c_low
                    sweep_idx = m_idx
                    break

        if not manipulation_found or sweep_peak is None:
            i += 1
            continue

        # 6. Gatillo M15: MSS Displacement + Entrada (Market Close vs FVG Consequent Encroachment)
        # Buscar el rango de velas M15 dentro de la ventana de análisis
        sweep_time = h1_times[sweep_idx]
        m15_start_idx = int(np.searchsorted(m15_times, sweep_time, side="left"))
        m15_limit_idx = min(len(m15_times) - 1, m15_start_idx + 24)

        if m15_limit_idx <= m15_start_idx + 4 or m15_start_idx <= busy_until_m15:
            i += 1
            continue

        mss_found = False
        entry_price = None
        stop_loss = None
        fill_bar_idx = None
        min_body = 0.45


        for cand_k in range(m15_start_idx + 2, m15_limit_idx):
            m_close = m15_closes[cand_k]
            m_open = m15_opens[cand_k]
            m_high = m15_highs[cand_k]
            m_low = m15_lows[cand_k]
            m_body = abs(m_close - m_open)
            m_range = m_high - m_low + 1e-9

            # MSS Displacement Candle
            if (m_body / m_range) < min_body:
                continue

            if intended_direction == "SELL":
                # Rompe soporte previo
                local_support = np.min(m15_lows[max(0, cand_k - 8):cand_k])
                if m_close >= local_support:
                    continue

                if mode == "baseline":
                    # Baseline entra al mercado al cierre de la vela de desplazamiento
                    entry_price = m_close
                    stop_loss = sweep_peak + spread
                    fill_bar_idx = cand_k + 1
                    mss_found = True
                    break
                else:
                    # Augmented v2.1: Entrada en Consequent Encroachment (50% FVG) o retest de soporte
                    fvg_top = m15_lows[cand_k - 2]
                    fvg_bottom = m15_highs[cand_k]
                    if fvg_top > fvg_bottom:
                        ce_fvg = (fvg_top + fvg_bottom) / 2.0
                        target_entry = min(local_support, ce_fvg)
                    else:
                        target_entry = local_support

                    # Verificar si en las siguientes 1-6 velas hay pullback que llena la orden
                    for pull_k in range(cand_k + 1, min(len(m15_times), cand_k + 7)):
                        if m15_highs[pull_k] >= target_entry:
                            # Orden ejecutada en pullback
                            entry_price = target_entry
                            stop_loss = sweep_peak + spread
                            fill_bar_idx = pull_k
                            mss_found = True
                            break
                        if m15_highs[pull_k] > sweep_peak:
                            break  # Invalidado antes de llenar
                    if mss_found:
                        break

            else:  # BUY
                # Rompe resistencia previa
                local_resistance = np.max(m15_highs[max(0, cand_k - 8):cand_k])
                if m_close <= local_resistance:
                    continue

                if mode == "baseline":
                    entry_price = m_close
                    stop_loss = sweep_peak - spread
                    fill_bar_idx = cand_k + 1
                    mss_found = True
                    break
                else:
                    fvg_bottom = m15_highs[cand_k - 2]
                    fvg_top = m15_lows[cand_k]
                    if fvg_top > fvg_bottom:
                        ce_fvg = (fvg_top + fvg_bottom) / 2.0
                        target_entry = max(local_resistance, ce_fvg)
                    else:
                        target_entry = local_resistance

                    # Verificar si en las siguientes 1-6 velas hay pullback que llena la orden
                    for pull_k in range(cand_k + 1, min(len(m15_times), cand_k + 7)):
                        if m15_lows[pull_k] <= target_entry:
                            entry_price = target_entry
                            stop_loss = sweep_peak - spread
                            fill_bar_idx = pull_k
                            mss_found = True
                            break
                        if m15_lows[pull_k] < sweep_peak:
                            break  # Invalidado antes de llenar
                    if mss_found:
                        break

        if not mss_found or entry_price is None or stop_loss is None or fill_bar_idx is None:
            i += 1
            continue

        fill_time = to_utc_timestamp(m15_times[fill_bar_idx])
        # Para mercados reales, la ejecución real del fill debe ocurrir dentro de Killzone y fuera de rollover/cierre
        if not is_synth:
            if is_market_closed_or_rollover(fill_time, is_synth) or not is_killzone_active(fill_time, is_synth, mode, cat=category):
                i += 1
                continue

        risk = abs(entry_price - stop_loss)
        if risk <= 0 or risk < (1.2 * spread):
            i += 1
            continue

        # Validación Fibonacci institucional (Discount / Premium):
        if intended_direction == "SELL":
            swing_low_impulse = float(np.min(h1_lows[sweep_idx : i + 1]))
            fibo_50 = (sweep_peak + swing_low_impulse) / 2.0
            if range_low >= fibo_50:
                i += 1
                continue
            tp1_price = entry_price - (2.0 * risk)
            tp2_price = entry_price - (3.5 * risk)
        else:
            swing_high_impulse = float(np.max(h1_highs[sweep_idx : i + 1]))
            fibo_50 = (sweep_peak + swing_high_impulse) / 2.0
            if range_high <= fibo_50:
                i += 1
                continue
            tp1_price = entry_price + (2.0 * risk)
            tp2_price = entry_price + (3.5 * risk)


        # 7. Ejecutar simulación dual leg bar-a-bar
        trade_res = simulate_trade_dual_leg(
            direction=intended_direction,
            fill_price=entry_price,
            stop_loss=stop_loss,
            tp1_price=tp1_price,
            tp2_price=tp2_price,
            m15_highs=m15_highs,
            m15_lows=m15_lows,
            m15_opens=m15_opens,
            m15_closes=m15_closes,
            start_bar=fill_bar_idx,
            spread=spread,
        )

        r_net, outcome, duration_bars, hit_tp1, hit_tp2, hit_be = trade_res
        busy_until_m15 = fill_bar_idx + duration_bars

        trade_time = pd.Timestamp(m15_times[fill_bar_idx])
        trades.append({
            "symbol": symbol,
            "category": category,
            "is_synth": is_synth,
            "mode": mode,
            "time": str(trade_time),
            "direction": intended_direction,
            "entry_price": round(entry_price, 5),
            "stop_loss": round(stop_loss, 5),
            "tp1_price": round(tp1_price, 5),
            "tp2_price": round(tp2_price, 5),
            "risk_pts": round(risk, 5),
            "r_multiple": round(r_net, 3),
            "outcome": outcome,
            "hit_tp1": hit_tp1,
            "hit_tp2": hit_tp2,
            "hit_be": hit_be,
            "bars": duration_bars,
        })

        # Avanzar H1 al cierre de este trade para evitar lookahead y solapamiento
        i = max(i + 1, int(np.searchsorted(h1_times, np.datetime64(trade_time.to_datetime64()), side="right")))

    return trades


def audit_all_symbols(symbols: list[str] | None = None) -> tuple[pd.DataFrame, pd.DataFrame]:
    if symbols is None:
        symbols = list(ASSET_UNIVERSE.keys())

    out_dir = PROJECT_ROOT / "storage" / "analysis"
    out_dir.mkdir(parents=True, exist_ok=True)

    print("=" * 100)
    print(f"AUDITORÍA INTEGRAL DE 2 AÑOS (OCTUBRE 2024 - OCTUBRE 2026): ESTRATEGIA ICT SABRI MALLE")
    print(f"Comparativa Causal: Baseline ICT vs Augmented ICT v2.1 (Consequent Encroachment 50% FVG & 24/7)")
    print(f"Total Activos a Auditar: {len(symbols)}")
    print("=" * 100)

    all_trades_baseline = []
    all_trades_augmented = []
    summary_rows = []

    t_start = time.time()

    for idx, sym in enumerate(symbols, start=1):
        is_synth = IS_SYNTH_MAP.get(sym, False)
        cat = ASSET_CATEGORIES.get(sym, "OTHER")
        print(f"[{idx:02d}/{len(symbols):02d}] {sym:<25} ({cat:<12}) ...", end=" ", flush=True)

        frames = load_dataset(sym)
        if frames is None:
            print("[ERROR: Sin datos H1/M15]")
            continue

        # 1. Baseline
        t_base = run_ict_replay_for_symbol(sym, frames, mode="baseline")
        all_trades_baseline.extend(t_base)

        # 2. Augmented v2.1
        t_aug = run_ict_replay_for_symbol(sym, frames, mode="augmented")
        all_trades_augmented.extend(t_aug)

        # Métricas Baseline
        n_b = len(t_base)
        wr_b = (sum(1 for t in t_base if t["hit_tp1"]) / n_b * 100.0) if n_b > 0 else 0.0
        r_b = sum(t["r_multiple"] for t in t_base)
        exp_b = (r_b / n_b) if n_b > 0 else 0.0

        # Métricas Augmented
        n_a = len(t_aug)
        wr_a = (sum(1 for t in t_aug if t["hit_tp1"]) / n_a * 100.0) if n_a > 0 else 0.0
        r_a = sum(t["r_multiple"] for t in t_aug)
        exp_a = (r_a / n_a) if n_a > 0 else 0.0

        diff_r = r_a - r_b
        diff_trades = n_a - n_b

        status_str = "PROFIT" if r_a > 0 else "LOSS"
        print(f"Base: {n_b:2d}tr ({wr_b:4.1f}% WR, {r_b:+6.2f}R) | Aug: {n_a:2d}tr ({wr_a:4.1f}% WR, {r_a:+6.2f}R) | Δ: {diff_trades:+2d}tr, {diff_r:+6.2f}R [{status_str}]")

        summary_rows.append({
            "symbol": sym,
            "category": cat,
            "is_synth": is_synth,
            # Baseline
            "base_trades": n_b,
            "base_win_rate_tp1": round(wr_b, 1),
            "base_net_r": round(r_b, 2),
            "base_exp_r": round(exp_b, 3),
            # Augmented v2.1
            "aug_trades": n_a,
            "aug_win_rate_tp1": round(wr_a, 1),
            "aug_win_rate_tp2": round((sum(1 for t in t_aug if t["hit_tp2"]) / n_a * 100.0) if n_a > 0 else 0.0, 1),
            "aug_tp1_hits": sum(1 for t in t_aug if t["hit_tp1"]),
            "aug_tp2_hits": sum(1 for t in t_aug if t["hit_tp2"]),
            "aug_be_hits": sum(1 for t in t_aug if t["hit_be"]),
            "aug_sl_hits": sum(1 for t in t_aug if t["outcome"] in ("SL_FULL", "TIMEOUT_SL")),
            "aug_net_r": round(r_a, 2),
            "aug_exp_r": round(exp_a, 3),
            "aug_delta_r": round(diff_r, 2),
            "aug_delta_trades": diff_trades,
            "recommendation": "ACTIVE" if (r_a > 0 and n_a >= 5 and wr_a >= 35.0) else "PRUNED",
        })

    t_elapsed = time.time() - t_start
    print("=" * 100)
    print(f"Auditoría completada en {t_elapsed:.1f} segundos.")

    df_summary = pd.DataFrame(summary_rows)
    df_trades = pd.DataFrame(all_trades_augmented)

    # Guardar CSVs
    summary_path = out_dir / "replay_ict_60_assets_2y_summary.csv"
    trades_path = out_dir / "replay_ict_60_assets_2y_trades.csv"
    df_summary.to_csv(summary_path, index=False)
    df_trades.to_csv(trades_path, index=False)

    print(f"Resumen guardado en: {summary_path}")
    print(f"Operaciones guardadas en: {trades_path}")

    # Totales Globales
    b_trades_tot = df_summary["base_trades"].sum()
    b_r_tot = df_summary["base_net_r"].sum()
    a_trades_tot = df_summary["aug_trades"].sum()
    a_r_tot = df_summary["aug_net_r"].sum()

    a_active = df_summary[df_summary["recommendation"] == "ACTIVE"]
    a_pruned = df_summary[df_summary["recommendation"] == "PRUNED"]

    print("\n" + "=" * 80)
    print("MÉTRICAS GLOBALES CONSOLIDADAS (60 ACTIVOS / 2 AÑOS):")
    print(f"• Baseline ICT:  {b_trades_tot} trades | {b_r_tot:+.2f} R netos")
    print(f"• Augmented ICT: {a_trades_tot} trades | {a_r_tot:+.2f} R netos (Δ: {a_trades_tot - b_trades_tot:+d} trades, {a_r_tot - b_r_tot:+.2f} R)")
    print(f"• Activos con Expectativa Positiva (ACTIVE): {len(a_active)} activos | +{a_active['aug_net_r'].sum():.2f} R")
    print(f"• Activos para Poda (PRUNED): {len(a_pruned)} activos | {a_pruned['aug_net_r'].sum():.2f} R")
    print("=" * 80)

    return df_summary, df_trades


def main():
    parser = argparse.ArgumentParser(description="Auditoría de 2 años ICT Sabri Malle sobre 60 activos.")
    parser.add_argument("--symbols", type=str, default="", help="Lista separada por comas de símbolos específicos.")
    args = parser.parse_args()

    symbols = [s.strip() for s in args.symbols.split(",") if s.strip()] if args.symbols else None
    audit_all_symbols(symbols)


if __name__ == "__main__":
    main()

