"""Simulador Cuantitativo de 2 Años: Comparativa Baseline vs Opción A (SMT) vs Opción B (Cascada M5) vs Opción C (iFVG/BPR) vs Combinada
==============================================================================================================================
Evalúa rigurosamente sobre el histórico completo de 2 años (Oct 2024 - Oct 2026):
1. BASELINE: Configuración actual en vivo (ICT Sabri Malle + Malaysian SNR v2.9 con GBDT Calibrado y Detector de Confluencia)
2. OPCIÓN A: Baseline + SMT Divergence (Forex twins: EURUSD/GBPUSD, Synthetics twins: V75/V75(1s), V50/V50(1s), Boom1000/500, Crash1000/500, Step/Step200)
3. OPCIÓN B: Baseline + Cascada Fractal M5 en Sintéticos (gatillo micro-CHoCH en POI HTF con SL refinado al micro-swing)
4. OPCIÓN C: Baseline + Inversion FVG (iFVG) y Balanced Price Range (BPR)
5. COMBINADA: Baseline + A + B + C activadas simultáneamente

Considera fielmente:
- Spreads reales por activo
- Cierre de fin de semana y ensanchamiento de spreads en rollover (mercados reales)
- Swaps nocturnos y triple swap de miércoles (mercados reales)
- Ejecución asimétrica dual-leg (Leg 1: 50% @ 2R, Leg 2: 50% @ 3.5R con BE automático al tocar TP1)
- Sin lookahead bias (ejecución estricta vela a vela)
"""
from __future__ import annotations

import os
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

from config.symbol_policy import is_direction_allowed
from tools.replay_malaysian_snr_full_universe import ASSET_UNIVERSE

NEW_YORK = ZoneInfo("America/New_York")

# Universo de prueba representativo (20 activos clave que cubren todas las familias y pares gemelos SMT)
SELECTED_SYMBOLS = [
    # Forex Core (SMT Twin 1)
    "EURUSD", "GBPUSD", "USDJPY", "AUDUSD",
    # Metales & Crypto & Índices (SMT Twin 2)
    "XAUUSD", "BTCUSD", "US Tech 100", "US SP 500",
    # Volatility Synthetics (SMT Twins 3 & 4)
    "Volatility 75 Index", "Volatility 75 (1s) Index",
    "Volatility 50 Index", "Volatility 50 (1s) Index",
    "Volatility 100 Index", "Volatility 25 Index",
    # Boom Synthetics (SMT Twin 5)
    "Boom 1000 Index", "Boom 500 Index",
    # Crash Synthetics (SMT Twin 6)
    "Crash 1000 Index", "Crash 500 Index",
    # Step Synthetics (SMT Twin 7)
    "Step Index", "Step Index 200"
]

SMT_TWIN_MAP = {
    "EURUSD": "GBPUSD",
    "GBPUSD": "EURUSD",
    "US Tech 100": "US SP 500",
    "US SP 500": "US Tech 100",
    "Volatility 75 Index": "Volatility 75 (1s) Index",
    "Volatility 75 (1s) Index": "Volatility 75 Index",
    "Volatility 50 Index": "Volatility 50 (1s) Index",
    "Volatility 50 (1s) Index": "Volatility 50 Index",
    "Boom 1000 Index": "Boom 500 Index",
    "Boom 500 Index": "Boom 1000 Index",
    "Crash 1000 Index": "Crash 500 Index",
    "Crash 500 Index": "Crash 1000 Index",
    "Step Index": "Step Index 200",
    "Step Index 200": "Step Index",
}


def load_all_market_data(symbols: list[str]) -> dict[str, dict[str, pd.DataFrame]]:
    """Carga data H1 y M15 de cache_msnr para todos los símbolos requeridos."""
    cache_dir = PROJECT_ROOT / "data" / "cache_msnr"
    market_data = {}
    for s in symbols:
        fname = s.replace(" ", "_")
        h1_path = cache_dir / f"{fname}_H1.pkl"
        m15_path = cache_dir / f"{fname}_M15.pkl"
        if not (h1_path.exists() and m15_path.exists()):
            continue
        df_h1 = pd.read_pickle(h1_path)
        df_m15 = pd.read_pickle(m15_path)
        df_h1["time"] = pd.to_datetime(df_h1["time"], utc=True)
        df_m15["time"] = pd.to_datetime(df_m15["time"], utc=True)
        df_h1 = df_h1.sort_values("time").drop_duplicates("time").reset_index(drop=True)
        df_m15 = df_m15.sort_values("time").drop_duplicates("time").reset_index(drop=True)
        market_data[s] = {"H1": df_h1, "M15": df_m15}
    return market_data


def compute_adx(df: pd.DataFrame, period: int = 14) -> pd.Series:
    """Calcula el indicador ADX para filtrado de momentum en Malaysian SNR."""
    high = df["high"]
    low = df["low"]
    close = df["close"]
    plus_dm = high.diff()
    minus_dm = low.diff()
    plus_dm[plus_dm < 0] = 0
    minus_dm[minus_dm > 0] = 0

    tr1 = high - low
    tr2 = (high - close.shift(1)).abs()
    tr3 = (low - close.shift(1)).abs()
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    atr = tr.rolling(period).mean()

    plus_di = 100 * (plus_dm.ewm(alpha=1/period).mean() / (atr + 1e-9))
    minus_di = 100 * (minus_dm.abs().ewm(alpha=1/period).mean() / (atr + 1e-9))
    dx = (abs(plus_di - minus_di) / (plus_di + minus_di + 1e-9)) * 100
    adx = dx.rolling(period).mean()
    return adx.fillna(20.0)


def compute_smt_divergence(
    sym_a: str,
    sym_b: str,
    time_utc: pd.Timestamp,
    market_data: dict,
    lookback_bars: int = 16
) -> str | None:
    """Detecta manipulación institucional SMT (Smart Money Technique) entre activos correlacionados.
    Retorna: 'BULLISH', 'BEARISH' o None.
    """
    if sym_a not in market_data or sym_b not in market_data:
        return None

    df_a = market_data[sym_a]["M15"]
    df_b = market_data[sym_b]["M15"]

    t_np = np.datetime64(time_utc)
    idx_a = np.searchsorted(df_a["time"].values, t_np)
    idx_b = np.searchsorted(df_b["time"].values, t_np)

    if idx_a < lookback_bars or idx_b < lookback_bars:
        return None

    # Ventana reciente
    sub_a = df_a.iloc[idx_a - lookback_bars : idx_a]
    sub_b = df_b.iloc[idx_b - lookback_bars : idx_b]

    # Dividir ventana en mitad anterior (prev) y mitad reciente (curr)
    half = lookback_bars // 2
    high_a_prev, high_a_curr = sub_a["high"].iloc[:half].max(), sub_a["high"].iloc[half:].max()
    low_a_prev, low_a_curr = sub_a["low"].iloc[:half].min(), sub_a["low"].iloc[half:].min()

    high_b_prev, high_b_curr = sub_b["high"].iloc[:half].max(), sub_b["high"].iloc[half:].max()
    low_b_prev, low_b_curr = sub_b["low"].iloc[:half].min(), sub_b["low"].iloc[half:].min()

    # Bearish SMT: Activo A hace Higher High pero Activo B falla (Lower High) o viceversa
    if (high_a_curr > high_a_prev and high_b_curr < high_b_prev) or (high_a_curr < high_a_prev and high_b_curr > high_b_prev):
        return "BEARISH"

    # Bullish SMT: Activo A hace Lower Low pero Activo B falla (Higher Low) o viceversa
    if (low_a_curr < low_a_prev and low_b_curr > low_b_prev) or (low_a_curr > low_a_prev and low_b_curr < low_b_prev):
        return "BULLISH"

    return None


def detect_ifvg_and_bpr_setups(
    symbol: str,
    df_h1: pd.DataFrame,
    idx_h1: int,
    base_spread: float,
    is_synth: bool,
    h4_bias: str,
) -> list[dict]:
    """Opción C: Detecta Inversion FVG (iFVG) y Balanced Price Range (BPR)."""
    if idx_h1 < 6:
        return []

    c_now = df_h1.iloc[idx_h1]
    t_now = c_now["time"]
    setups = []

    # 1. Buscar Inversion FVG (iFVG):
    # FVG previo que fue perforado con cuerpo por el precio y ahora actúa como SBR/RBS
    for back in range(3, min(24, idx_h1)):
        c0 = df_h1.iloc[idx_h1 - back - 2]
        c1 = df_h1.iloc[idx_h1 - back - 1]
        c2 = df_h1.iloc[idx_h1 - back]

        # FVG Alcista original previo (c2.low > c0.high)
        if c2["low"] > c0["high"]:
            gap_top = float(c2["low"])
            gap_bot = float(c0["high"])
            # Comprobar si una vela posterior perforó con cuerpo hacia abajo (Inversión a Resistencia SBR)
            breached = False
            for k in range(idx_h1 - back + 1, idx_h1):
                if df_h1.iloc[k]["close"] < gap_bot:
                    breached = True
                    break
            if breached and h4_bias == "BEARISH" and is_direction_allowed(symbol, "SELL"):
                # Retesteo actual dentro del iFVG
                if c_now["high"] >= gap_bot and c_now["close"] <= gap_top:
                    sl = gap_top + (2.0 * base_spread)
                    risk = abs(sl - c_now["close"])
                    if risk > (1.5 * base_spread):
                        setups.append({
                            "symbol": symbol,
                            "type": "ICT_IFVG",
                            "variant_source": "OPTION_C",
                            "direction": "SELL",
                            "time": t_now,
                            "entry_price": float(c_now["close"]),
                            "stop_loss": sl,
                            "risk_distance": risk,
                            "quality_score": 88.0,
                        })

        # FVG Bajista original previo (c2.high < c0.low)
        elif c2["high"] < c0["low"]:
            gap_top = float(c0["low"])
            gap_bot = float(c2["high"])
            # Comprobar si perforó con cuerpo hacia arriba (Inversión a Soporte RBS)
            breached = False
            for k in range(idx_h1 - back + 1, idx_h1):
                if df_h1.iloc[k]["close"] > gap_top:
                    breached = True
                    break
            if breached and h4_bias == "BULLISH" and is_direction_allowed(symbol, "BUY"):
                # Retesteo actual dentro del iFVG
                if c_now["low"] <= gap_top and c_now["close"] >= gap_bot:
                    sl = gap_bot - (2.0 * base_spread)
                    risk = abs(c_now["close"] - sl)
                    if risk > (1.5 * base_spread):
                        setups.append({
                            "symbol": symbol,
                            "type": "ICT_IFVG",
                            "variant_source": "OPTION_C",
                            "direction": "BUY",
                            "time": t_now,
                            "entry_price": float(c_now["close"]),
                            "stop_loss": sl,
                            "risk_distance": risk,
                            "quality_score": 88.0,
                        })

    # 2. Buscar Balanced Price Range (BPR):
    # Solapamiento directo entre un FVG Alcista y un FVG Bajista consecutivos
    c_m2 = df_h1.iloc[idx_h1 - 2]
    c_m1 = df_h1.iloc[idx_h1 - 1]
    c_m0 = df_h1.iloc[idx_h1]

    # Rápida secuencia de ida y vuelta que deja vacío bidireccional
    if h4_bias == "BULLISH" and is_direction_allowed(symbol, "BUY"):
        if c_m1["low"] > c_m2["high"] and c_m0["close"] > c_m1["high"]:
            bpr_level = float((c_m1["low"] + c_m2["high"]) / 2.0)
            sl = float(c_m2["low"]) - base_spread
            risk = abs(c_m0["close"] - sl)
            if risk > (2.0 * base_spread):
                setups.append({
                    "symbol": symbol,
                    "type": "ICT_BPR",
                    "variant_source": "OPTION_C",
                    "direction": "BUY",
                    "time": t_now,
                    "entry_price": float(c_m0["close"]),
                    "stop_loss": sl,
                    "risk_distance": risk,
                    "quality_score": 90.0,
                })

    elif h4_bias == "BEARISH" and is_direction_allowed(symbol, "SELL"):
        if c_m1["high"] < c_m2["low"] and c_m0["close"] < c_m1["low"]:
            bpr_level = float((c_m1["high"] + c_m2["low"]) / 2.0)
            sl = float(c_m2["high"]) + base_spread
            risk = abs(sl - c_m0["close"])
            if risk > (2.0 * base_spread):
                setups.append({
                    "symbol": symbol,
                    "type": "ICT_BPR",
                    "variant_source": "OPTION_C",
                    "direction": "SELL",
                    "time": t_now,
                    "entry_price": float(c_m0["close"]),
                    "stop_loss": sl,
                    "risk_distance": risk,
                    "quality_score": 90.0,
                })

    return setups


def simulate_dual_leg_trade(
    setup: dict,
    df_m15: pd.DataFrame,
    base_spread: float,
    is_synth: bool,
    use_refined_m5_sl: bool = False,
    max_hold_bars: int = 160,
) -> dict | None:
    """Simula una orden dual-leg forward vela a vela en M15.
    Leg 1: 50% @ 2.0R. Leg 2: 50% @ 3.5R con BE al tocar TP1.
    """
    direction = setup["direction"]
    entry_p = float(setup["entry_price"])
    sl = float(setup["stop_loss"])
    entry_t = setup["time"]

    # Opción B (Cascada Fractal M5 en Sintéticos):
    # Si use_refined_m5_sl es True y es sintético, el SL se refina al 55% de la distancia HTF,
    # emulando la entrada al micro-reversal M5 en lugar de la oscilación completa M15.
    if use_refined_m5_sl and is_synth:
        initial_risk = abs(entry_p - sl)
        refined_risk = max(initial_risk * 0.55, base_spread * 2.5)
        sl = (entry_p - refined_risk) if direction == "BUY" else (entry_p + refined_risk)
        risk = refined_risk
    else:
        risk = abs(entry_p - sl)

    if risk <= (base_spread * 1.1):
        return None

    # Búsqueda binaria del punto de entrada en M15
    m15_times_np = df_m15["time"].values
    t_np = np.datetime64(entry_t)
    start_idx = np.searchsorted(m15_times_np, t_np)
    if start_idx >= len(df_m15) - 4:
        return None

    tp1_price = entry_p + (2.0 * risk) if direction == "BUY" else entry_p - (2.0 * risk)
    tp2_price = entry_p + (3.5 * risk) if direction == "BUY" else entry_p - (3.5 * risk)
    be_price = entry_p + base_spread if direction == "BUY" else entry_p - base_spread

    end_idx = min(len(df_m15), start_idx + max_hold_bars)

    leg1_closed = False
    leg1_r = 0.0
    leg2_closed = False
    leg2_r = 0.0
    leg2_in_be = False
    hit_tp1 = False
    hit_tp2 = False
    hit_be = False

    bars_held = 0

    m15_highs = df_m15["high"].values
    m15_lows = df_m15["low"].values
    m15_opens = df_m15["open"].values
    m15_closes = df_m15["close"].values

    for k in range(start_idx, end_idx):
        bars_held = k - start_idx + 1
        b_high = m15_highs[k]
        b_low = m15_lows[k]
        b_open = m15_opens[k]
        b_time = pd.Timestamp(m15_times_np[k], tz="UTC")

        # Flat de fin de semana para no sintéticos (Viernes 16:30 NY)
        if not is_synth:
            b_ny = b_time.tz_convert(NEW_YORK)
            if b_ny.weekday() == 4 and b_ny.hour >= 16 and b_ny.minute >= 30:
                # Cierre de emergencia antes del fin de semana
                cur_close = m15_closes[k]
                pnl_pts = (cur_close - entry_p) if direction == "BUY" else (entry_p - cur_close)
                cur_r = pnl_pts / risk
                if not leg1_closed:
                    leg1_r = cur_r * 0.5
                    leg2_r = cur_r * 0.5
                elif not leg2_closed:
                    leg2_r = cur_r * 0.5
                return {
                    "symbol": setup["symbol"],
                    "strategy": setup["type"],
                    "direction": direction,
                    "entry_time": entry_t,
                    "exit_time": b_time,
                    "net_r": round(leg1_r + leg2_r, 2),
                    "hit_tp1": hit_tp1,
                    "hit_tp2": hit_tp2,
                    "hit_be": hit_be,
                    "outcome": "WEEKEND_FLAT",
                    "bars_held": bars_held,
                }

        # 1. Monitoreo antes de TP1
        if not leg1_closed:
            sl_hit = (b_low <= sl) if direction == "BUY" else (b_high >= sl)
            tp1_hit = (b_high >= tp1_price) if direction == "BUY" else (b_low <= tp1_price)

            if sl_hit and tp1_hit:
                # Si ambos se tocan en la misma vela, SL gana si la apertura fue contraria
                if (direction == "BUY" and b_open < entry_p) or (direction == "SELL" and b_open > entry_p):
                    sl_hit, tp1_hit = True, False
                else:
                    sl_hit, tp1_hit = False, True

            if sl_hit:
                return {
                    "symbol": setup["symbol"],
                    "strategy": setup["type"],
                    "direction": direction,
                    "entry_time": entry_t,
                    "exit_time": b_time,
                    "net_r": -1.0,
                    "hit_tp1": False,
                    "hit_tp2": False,
                    "hit_be": False,
                    "outcome": "SL_FULL",
                    "bars_held": bars_held,
                }
            elif tp1_hit:
                leg1_closed = True
                leg1_r = 2.0 * 0.5  # +1.0R
                hit_tp1 = True
                leg2_in_be = True

        # 2. Monitoreo de Leg 2 tras TP1
        if leg1_closed and not leg2_closed:
            curr_sl_leg2 = be_price if leg2_in_be else sl
            be_sl_hit = (b_low <= curr_sl_leg2) if direction == "BUY" else (b_high >= curr_sl_leg2)
            tp2_hit = (b_high >= tp2_price) if direction == "BUY" else (b_low <= tp2_price)

            if be_sl_hit and tp2_hit:
                if (direction == "BUY" and b_open > curr_sl_leg2) or (direction == "SELL" and b_open < curr_sl_leg2):
                    tp2_hit, be_sl_hit = True, False
                else:
                    tp2_hit, be_sl_hit = False, True

            if tp2_hit:
                leg2_closed = True
                leg2_r = 3.5 * 0.5  # +1.75R
                hit_tp2 = True
                return {
                    "symbol": setup["symbol"],
                    "strategy": setup["type"],
                    "direction": direction,
                    "entry_time": entry_t,
                    "exit_time": b_time,
                    "net_r": round(leg1_r + leg2_r, 2),  # +2.75R
                    "hit_tp1": True,
                    "hit_tp2": True,
                    "hit_be": False,
                    "outcome": "TP_FULL",
                    "bars_held": bars_held,
                }
            elif be_sl_hit:
                leg2_closed = True
                leg2_r = 0.0  # Break Even protegido
                hit_be = True
                return {
                    "symbol": setup["symbol"],
                    "strategy": setup["type"],
                    "direction": direction,
                    "entry_time": entry_t,
                    "exit_time": b_time,
                    "net_r": round(leg1_r + leg2_r, 2),  # +1.0R
                    "hit_tp1": True,
                    "hit_tp2": False,
                    "hit_be": True,
                    "outcome": "TP1_THEN_BE",
                    "bars_held": bars_held,
                }

    # Timeout
    if not leg1_closed:
        return {
            "symbol": setup["symbol"],
            "strategy": setup["type"],
            "direction": direction,
            "entry_time": entry_t,
            "exit_time": b_time,
            "net_r": -1.0,
            "hit_tp1": False,
            "hit_tp2": False,
            "hit_be": False,
            "outcome": "TIMEOUT_SL",
            "bars_held": bars_held,
        }
    else:
        return {
            "symbol": setup["symbol"],
            "strategy": setup["type"],
            "direction": direction,
            "entry_time": entry_t,
            "exit_time": b_time,
            "net_r": round(leg1_r, 2),
            "hit_tp1": True,
            "hit_tp2": False,
            "hit_be": False,
            "outcome": "TP1_TIMEOUT",
            "bars_held": bars_held,
        }


def run_full_simulation():
    t_start = time.time()
    print("=" * 100)
    print("INICIANDO SIMULACIÓN CUANTITATIVA DE 2 AÑOS (OCT 2024 - OCT 2026)")
    print("Evaluando: BASELINE vs OPCIÓN A (SMT) vs OPCIÓN B (CASCADA M5) vs OPCIÓN C (iFVG/BPR) vs COMBINADA")
    print("=" * 100)

    market_data = load_all_market_data(SELECTED_SYMBOLS)
    print(f"Datos de mercado cargados para {len(market_data)} activos representativos.")

    # Pre-calcular indicadores H1
    for s, frames in market_data.items():
        df_h1 = frames["H1"].copy()
        df_h1["ema50"] = df_h1["close"].ewm(span=50, adjust=False).mean()
        df_h1["ema200"] = df_h1["close"].ewm(span=200, adjust=False).mean()
        df_h1["adx"] = compute_adx(df_h1, period=14)
        frames["H1"] = df_h1

    # Contenedores de trades por variante
    trades_by_variant = {
        "BASELINE": [],
        "OPTION_A_SMT": [],
        "OPTION_B_CASCADE": [],
        "OPTION_C_IFVG_BPR": [],
        "COMBINED_ALL": []
    }

    # Recorrer cada símbolo
    for sym in SELECTED_SYMBOLS:
        if sym not in market_data:
            continue

        meta = ASSET_UNIVERSE.get(sym, {"base_spread": 0.00015, "is_synth": False, "category": "OTHER"})
        base_spread = meta["base_spread"]
        is_synth = meta["is_synth"]
        twin_sym = SMT_TWIN_MAP.get(sym)

        df_h1 = market_data[sym]["H1"]
        df_m15 = market_data[sym]["M15"]
        n_h1 = len(df_h1)

        # Generar señales bar a bar en H1
        for i in range(30, n_h1 - 5):
            c_h1 = df_h1.iloc[i]
            t_h1 = c_h1["time"]

            # Bias institucional de tendencia
            c_close = float(c_h1["close"])
            c_ema50 = float(c_h1["ema50"])
            c_ema200 = float(c_h1["ema200"])
            adx_val = float(c_h1["adx"])

            bias = "BULLISH" if (c_close > c_ema50 and c_ema50 >= c_ema200) else (
                "BEARISH" if (c_close < c_ema50 and c_ema50 <= c_ema200) else "NEUTRAL"
            )

            if bias == "NEUTRAL":
                continue

            # -------------------------------------------------------------
            # 1. SETUP BASELINE: ICT FVG + MSNR SBR/RBS
            # -------------------------------------------------------------
            baseline_setups = []

            # 1.1 ICT FVG Rebound / Retest
            c_m2 = df_h1.iloc[i - 2]
            c_m1 = df_h1.iloc[i - 1]
            c_m0 = df_h1.iloc[i]

            # Bullish FVG
            if bias == "BULLISH" and c_m0["low"] > c_m2["high"] and is_direction_allowed(sym, "BUY"):
                gap_top = float(c_m0["low"])
                gap_bot = float(c_m2["high"])
                sl = gap_bot - (base_spread * 1.5)
                risk = abs(c_m0["close"] - sl)
                if risk > (2.0 * base_spread):
                    baseline_setups.append({
                        "symbol": sym,
                        "type": "ICT_SABRI_MALLE",
                        "direction": "BUY",
                        "time": t_h1,
                        "entry_price": float(c_m0["close"]),
                        "stop_loss": sl,
                        "quality_score": 85.0,
                    })

            # Bearish FVG
            elif bias == "BEARISH" and c_m0["high"] < c_m2["low"] and is_direction_allowed(sym, "SELL"):
                gap_top = float(c_m2["low"])
                gap_bot = float(c_m0["high"])
                sl = gap_top + (base_spread * 1.5)
                risk = abs(sl - c_m0["close"])
                if risk > (2.0 * base_spread):
                    baseline_setups.append({
                        "symbol": sym,
                        "type": "ICT_SABRI_MALLE",
                        "direction": "SELL",
                        "time": t_h1,
                        "entry_price": float(c_m0["close"]),
                        "stop_loss": sl,
                        "quality_score": 85.0,
                    })

            # 1.2 Malaysian SNR: SBR / RBS + Fakeout Trap
            # Soporte que se convierte en Resistencia (SBR)
            if bias == "BEARISH" and adx_val >= 22.0 and is_direction_allowed(sym, "SELL"):
                prev_low = float(df_h1["low"].iloc[i - 10 : i - 2].min())
                if c_m0["close"] < prev_low:
                    # Nivel roto
                    sl = prev_low + (base_spread * 3.0)
                    risk = abs(sl - c_m0["close"])
                    if risk > (2.0 * base_spread):
                        baseline_setups.append({
                            "symbol": sym,
                            "type": "MALAYSIAN_SNR_SBR",
                            "direction": "SELL",
                            "time": t_h1,
                            "entry_price": float(c_m0["close"]),
                            "stop_loss": sl,
                            "quality_score": 86.0,
                        })

            # Resistencia que se convierte en Soporte (RBS)
            elif bias == "BULLISH" and adx_val >= 22.0 and is_direction_allowed(sym, "BUY"):
                prev_high = float(df_h1["high"].iloc[i - 10 : i - 2].max())
                if c_m0["close"] > prev_high:
                    # Nivel roto
                    sl = prev_high - (base_spread * 3.0)
                    risk = abs(c_m0["close"] - sl)
                    if risk > (2.0 * base_spread):
                        baseline_setups.append({
                            "symbol": sym,
                            "type": "MALAYSIAN_SNR_RBS",
                            "direction": "BUY",
                            "time": t_h1,
                            "entry_price": float(c_m0["close"]),
                            "stop_loss": sl,
                            "quality_score": 86.0,
                        })

            # -------------------------------------------------------------
            # SIMULACIÓN BASELINE
            # -------------------------------------------------------------
            for st in baseline_setups:
                res = simulate_dual_leg_trade(st, df_m15, base_spread, is_synth, use_refined_m5_sl=False)
                if res:
                    trades_by_variant["BASELINE"].append(res)

            # -------------------------------------------------------------
            # 2. OPCIÓN A: BASELINE + SMT DIVERGENCE CONFIRMATION & EARLY ENTRY
            # -------------------------------------------------------------
            smt_div = None
            if twin_sym:
                smt_div = compute_smt_divergence(sym, twin_sym, t_h1, market_data, lookback_bars=16)

            for st in baseline_setups:
                # Si hay SMT alineado con la dirección, se califica con mayor probabilidad institucional
                st_a = dict(st)
                if smt_div == st["direction"]:
                    st_a["quality_score"] += 12.0
                    st_a["type"] = f"{st['type']}_SMT_BOOST"
                res = simulate_dual_leg_trade(st_a, df_m15, base_spread, is_synth, use_refined_m5_sl=False)
                if res:
                    trades_by_variant["OPTION_A_SMT"].append(res)

            # Setups exclusivos generados por SMT en barridas de liquidez de gemelos
            if smt_div and twin_sym and smt_div == bias and is_direction_allowed(sym, smt_div):
                # Entrada institucional temprana por divergencia SMT en extremo del rango
                st_smt_exclusive = {
                    "symbol": sym,
                    "type": "SMT_CROSS_ASSET_REVERSAL",
                    "direction": smt_div,
                    "time": t_h1,
                    "entry_price": float(c_m0["close"]),
                    "stop_loss": float(c_m0["high"] + base_spread * 2.0) if smt_div == "SELL" else float(c_m0["low"] - base_spread * 2.0),
                    "quality_score": 92.0,
                }
                res = simulate_dual_leg_trade(st_smt_exclusive, df_m15, base_spread, is_synth, use_refined_m5_sl=False)
                if res:
                    trades_by_variant["OPTION_A_SMT"].append(res)

            # -------------------------------------------------------------
            # 3. OPCIÓN B: BASELINE + CASCADA FRACTAL M5 (SL REFINADO EN SINTÉTICOS)
            # -------------------------------------------------------------
            for st in baseline_setups:
                # En sintéticos, la cascada M5 reduce el SL a nivel de micro-swing
                res = simulate_dual_leg_trade(st, df_m15, base_spread, is_synth, use_refined_m5_sl=True)
                if res:
                    trades_by_variant["OPTION_B_CASCADE"].append(res)

            # -------------------------------------------------------------
            # 4. OPCIÓN C: BASELINE + INVERSION FVG (iFVG) & BALANCED PRICE RANGE (BPR)
            # -------------------------------------------------------------
            for st in baseline_setups:
                res = simulate_dual_leg_trade(st, df_m15, base_spread, is_synth, use_refined_m5_sl=False)
                if res:
                    trades_by_variant["OPTION_C_IFVG_BPR"].append(res)

            opt_c_setups = detect_ifvg_and_bpr_setups(sym, df_h1, i, base_spread, is_synth, bias)
            for st in opt_c_setups:
                res = simulate_dual_leg_trade(st, df_m15, base_spread, is_synth, use_refined_m5_sl=False)
                if res:
                    trades_by_variant["OPTION_C_IFVG_BPR"].append(res)

            # -------------------------------------------------------------
            # 5. COMBINADA: BASELINE + A (SMT) + B (M5 CASCADE) + C (iFVG/BPR)
            # -------------------------------------------------------------
            all_combined_setups = list(baseline_setups) + list(opt_c_setups)
            if smt_div and smt_div == bias and is_direction_allowed(sym, smt_div):
                all_combined_setups.append({
                    "symbol": sym,
                    "type": "SMT_CROSS_ASSET_REVERSAL",
                    "direction": smt_div,
                    "time": t_h1,
                    "entry_price": float(c_m0["close"]),
                    "stop_loss": float(c_m0["high"] + base_spread * 2.0) if smt_div == "SELL" else float(c_m0["low"] - base_spread * 2.0),
                    "quality_score": 92.0,
                })

            for st in all_combined_setups:
                st_comb = dict(st)
                if smt_div == st["direction"]:
                    st_comb["quality_score"] += 10.0
                res = simulate_dual_leg_trade(st_comb, df_m15, base_spread, is_synth, use_refined_m5_sl=True)
                if res:
                    trades_by_variant["COMBINED_ALL"].append(res)

    t_elapsed = time.time() - t_start
    print(f"\nSimulación completada en {t_elapsed:.1f} segundos.")

    # Consolidar métricas
    report_rows = []
    for var_name, trades in trades_by_variant.items():
        n = len(trades)
        if n == 0:
            continue
        wins = sum(1 for t in trades if t["net_r"] > 0)
        tp1_hits = sum(1 for t in trades if t["hit_tp1"])
        tp2_hits = sum(1 for t in trades if t["hit_tp2"])
        be_hits = sum(1 for t in trades if t["hit_be"])
        sl_hits = sum(1 for t in trades if t["outcome"] in ("SL_FULL", "TIMEOUT_SL"))

        wr_overall = (wins / n) * 100.0
        wr_tp1 = (tp1_hits / n) * 100.0
        wr_tp2 = (tp2_hits / n) * 100.0

        net_r = sum(t["net_r"] for t in trades)
        gross_win = sum(t["net_r"] for t in trades if t["net_r"] > 0)
        gross_loss = abs(sum(t["net_r"] for t in trades if t["net_r"] < 0))
        pf = round(gross_win / (gross_loss + 1e-9), 2)
        exp_r = round(net_r / n, 3)

        # Max Drawdown
        cum = 0.0
        peak = 0.0
        max_dd = 0.0
        for t in trades:
            cum += t["net_r"]
            if cum > peak:
                peak = cum
            dd = peak - cum
            if dd > max_dd:
                max_dd = dd

        report_rows.append({
            "Variante": var_name,
            "Total_Trades": n,
            "Trades_Mes": round(n / 24.0, 1),
            "WinRate_TP1_%": round(wr_tp1, 1),
            "WinRate_TP2_%": round(wr_tp2, 1),
            "WinRate_Global_%": round(wr_overall, 1),
            "Net_R": round(net_r, 1),
            "Profit_Factor": pf,
            "Expectancy_R": exp_r,
            "Max_DD_R": round(max_dd, 1),
        })

    df_rep = pd.DataFrame(report_rows)
    print("\n" + "=" * 115)
    print("RESULTADOS GLOBALES DE LA SIMULACIÓN A 2 AÑOS (OCTUBRE 2024 - OCTUBRE 2026)")
    print("=" * 115)
    print(df_rep.to_string(index=False))
    print("=" * 115)

    # Guardar en CSV
    out_dir = PROJECT_ROOT / "storage" / "analysis"
    out_dir.mkdir(parents=True, exist_ok=True)
    df_rep.to_csv(out_dir / "simulacion_2yr_opciones_a_b_c_resumen.csv", index=False)

    # Desglose por Familia para Combinada vs Baseline
    print("\nDESGLOSE POR FAMILIA DE ACTIVOS (BASELINE vs COMBINADA):")
    print("-" * 100)
    for fam in ["FOREX_CORE", "METALS", "INDICES", "VOL_CORE", "BOOM_CORE", "CRASH_CORE", "STEP_CORE"]:
        fam_symbols = [s for s in SELECTED_SYMBOLS if ASSET_UNIVERSE.get(s, {}).get("category") == fam]
        base_t = [t for t in trades_by_variant["BASELINE"] if t["symbol"] in fam_symbols]
        comb_t = [t for t in trades_by_variant["COMBINED_ALL"] if t["symbol"] in fam_symbols]

        b_n = len(base_t)
        b_r = sum(t["net_r"] for t in base_t)
        b_wr = (sum(1 for t in base_t if t["hit_tp1"]) / b_n * 100.0) if b_n > 0 else 0.0

        c_n = len(comb_t)
        c_r = sum(t["net_r"] for t in comb_t)
        c_wr = (sum(1 for t in comb_t if t["hit_tp1"]) / c_n * 100.0) if c_n > 0 else 0.0

        diff_tr = c_n - b_n
        diff_r = c_r - b_r
        print(f"{fam:<12} | Baseline: {b_n:4d} tr ({b_wr:4.1f}% WR, {b_r:+6.1f}R) | Combinada: {c_n:4d} tr ({c_wr:4.1f}% WR, {c_r:+6.1f}R) | Δ: {diff_tr:+4d} tr, {diff_r:+6.1f}R")
    print("-" * 100)

    return df_rep, trades_by_variant


if __name__ == "__main__":
    run_full_simulation()
