"""Replay institucional de 2 años de la estrategia ICT (Sabri Malle / AMD + FVG Rejection)
sobre todos los activos disponibles, con gestión de posición dual (2 entradas al 0.5% del capital)
y generación de dataset enriquecido para Meta-Etiquetado.
"""

from __future__ import annotations
import os
import glob
import math
import time
from datetime import datetime, timezone
from pathlib import Path
import numpy as np
import pandas as pd

HISTORICAL_DIRS = [
    Path("data/forex_historical"),
    Path("data/historical")
]

OUTPUT_DIR = Path("storage")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

SPREADS = {
    # Forex
    "AUDUSD": 0.00015,
    "EURUSD": 0.00012,
    "GBPUSD": 0.00018,
    "USDCAD": 0.00016,
    "USDCHF": 0.00015,
    "USDJPY": 0.015,
    # Crypto / Commodities / Indices
    "BTCUSD": 18.0,
    "US_Oil": 0.15,
    "US_SP_500": 0.35,
    "US_Tech_100": 0.90,
    "Wall_Street_30": 1.80,
    "XAGUSD": 0.05,
    "XAUUSD": 0.50,
    # Sintéticos
    "Boom_1000_Index": 0.20,
    "Crash_1000_Index": 0.20,
    "Jump_50_Index": 0.50,
    "Step_Index": 0.10,
    "Volatility_75_Index": 25.0,
    "Volatility_100_Index": 1.5,
}

ASSET_CLASSES = {
    "AUDUSD": "forex", "EURUSD": "forex", "GBPUSD": "forex",
    "USDCAD": "forex", "USDCHF": "forex", "USDJPY": "forex",
    "BTCUSD": "crypto", "US_Oil": "commodity",
    "US_SP_500": "index", "US_Tech_100": "index", "Wall_Street_30": "index",
    "XAGUSD": "metal", "XAUUSD": "metal",
    "Boom_1000_Index": "synthetic", "Crash_1000_Index": "synthetic",
    "Jump_50_Index": "synthetic", "Step_Index": "synthetic",
    "Volatility_75_Index": "synthetic", "Volatility_100_Index": "synthetic"
}

def load_instrument_data(symbol: str) -> tuple[pd.DataFrame | None, pd.DataFrame | None]:
    """Carga H1 y LTF (M15 o M5) para un símbolo dado."""
    h1_file = None
    ltf_file = None
    
    for base_dir in HISTORICAL_DIRS:
        h1_candidate = base_dir / f"{symbol}_H1.csv"
        if h1_candidate.exists():
            h1_file = h1_candidate
            
        m15_cand = base_dir / f"{symbol}_M15.csv"
        m5_cand = base_dir / f"{symbol}_M5.csv"
        if m15_cand.exists() and ltf_file is None:
            ltf_file = m15_cand
        elif m5_cand.exists() and ltf_file is None:
            ltf_file = m5_cand

    if not h1_file:
        return None, None

    df_h1 = pd.read_csv(h1_file)
    df_h1['time'] = pd.to_datetime(df_h1['time'], utc=True)
    df_h1 = df_h1.sort_values('time').reset_index(drop=True)

    if ltf_file and ltf_file.exists():
        df_ltf = pd.read_csv(ltf_file)
        df_ltf['time'] = pd.to_datetime(df_ltf['time'], utc=True)
        df_ltf = df_ltf.sort_values('time').reset_index(drop=True)
    else:
        df_ltf = df_h1

    return df_h1, df_ltf

def compute_atr(df: pd.DataFrame, period: int = 14) -> np.ndarray:
    """Calcula el Average True Range (ATR)."""
    high = df['high'].values
    low = df['low'].values
    close = df['close'].values
    n = len(df)
    tr = np.zeros(n)
    tr[0] = high[0] - low[0]
    for i in range(1, n):
        tr[i] = max(high[i] - low[i], abs(high[i] - close[i - 1]), abs(low[i] - close[i - 1]))
    
    atr = np.zeros(n)
    atr[0] = tr[0]
    alpha = 1.0 / period
    for i in range(1, n):
        atr[i] = (alpha * tr[i]) + ((1.0 - alpha) * atr[i - 1])
    return atr

def build_h4_candles(df_h1: pd.DataFrame) -> pd.DataFrame:
    """Reconstruye velas H4 agregadas a partir de H1 asegurando índice temporal UTC."""
    df = df_h1.copy()
    h4 = df.set_index('time').resample('4h').agg({
        'open': 'first',
        'high': 'max',
        'low': 'min',
        'close': 'last',
        'tick_volume': 'sum'
    }).dropna().reset_index()
    h4['time'] = pd.to_datetime(h4['time'], utc=True)
    return h4

def find_active_fvgs_fast(h4_df: pd.DataFrame, h4_idx: int, lookback_bars: int = 40) -> list[dict]:
    """Detecta Fair Value Gaps activos en H4 hasta el índice h4_idx."""
    if h4_idx < 4:
        return []

    start_idx = max(2, h4_idx - lookback_bars)
    fvgs = []
    highs = h4_df['high'].values
    lows = h4_df['low'].values
    closes = h4_df['close'].values
    opens = h4_df['open'].values

    for i in range(start_idx, h4_idx + 1):
        # Bearish FVG: Low de i-2 > High de i
        if lows[i - 2] > highs[i] and closes[i - 1] < opens[i - 1]:
            gap_top = lows[i - 2]
            gap_bottom = highs[i]
            mitigated = False
            for k in range(i + 1, h4_idx + 1):
                if highs[k] >= gap_top:
                    mitigated = True
                    break
            if not mitigated:
                fvgs.append({
                    'type': 'BEARISH',
                    'top': gap_top,
                    'bottom': gap_bottom,
                    'height': gap_top - gap_bottom,
                })

        # Bullish FVG: High de i-2 < Low de i
        if highs[i - 2] < lows[i] and closes[i - 1] > opens[i - 1]:
            gap_top = lows[i]
            gap_bottom = highs[i - 2]
            mitigated = False
            for k in range(i + 1, h4_idx + 1):
                if lows[k] <= gap_bottom:
                    mitigated = True
                    break
            if not mitigated:
                fvgs.append({
                    'type': 'BULLISH',
                    'top': gap_top,
                    'bottom': gap_bottom,
                    'height': gap_top - gap_bottom,
                })
    return fvgs

def detect_ict_sabri_malle_setups(
    symbol: str,
    df_h1: pd.DataFrame,
    df_h4: pd.DataFrame,
    spread: float,
    range_lookback: int = 24,
    min_rr_planned: float = 2.0
) -> list[dict]:
    """Escanea el historial de 2 años buscando setups estrictos de la estrategia ICT Sabri Malle."""
    setups = []
    atr_h1 = compute_atr(df_h1, period=14)
    
    # Calcular EMAs en H4
    df_h4['ema50'] = df_h4['close'].ewm(span=50, adjust=False).mean()
    df_h4['ema200'] = df_h4['close'].ewm(span=200, adjust=False).mean()
    
    h1_times = df_h1['time'].values
    h1_highs = df_h1['high'].values
    h1_lows = df_h1['low'].values
    h1_opens = df_h1['open'].values
    h1_closes = df_h1['close'].values
    
    h4_times = df_h4['time'].values
    h4_closes = df_h4['close'].values
    h4_ema50 = df_h4['ema50'].values
    h4_ema200 = df_h4['ema200'].values
    
    n_h1 = len(df_h1)
    
    i = max(range_lookback + 5, 200)
    while i < n_h1 - 24:
        c_time = h1_times[i]
        
        # Búsqueda rápida de H4 correspondiente con np.searchsorted
        h4_idx = np.searchsorted(h4_times, c_time, side='right') - 1
        if h4_idx < 30:
            i += 1
            continue
            
        c_h4_close = h4_closes[h4_idx]
        c_h4_ema50 = h4_ema50[h4_idx]
        c_h4_ema200 = h4_ema200[h4_idx]
        
        bias_bearish = (c_h4_close < c_h4_ema50) and (c_h4_ema50 <= c_h4_ema200)
        bias_bullish = (c_h4_close > c_h4_ema50) and (c_h4_ema50 >= c_h4_ema200)
        
        if not (bias_bearish or bias_bullish):
            i += 1
            continue
            
        # 2. Acumulación (A): Rango previo de 24 velas
        r_slice_high = h1_highs[i - range_lookback : i]
        r_slice_low = h1_lows[i - range_lookback : i]
        range_high = float(np.max(r_slice_high))
        range_low = float(np.min(r_slice_low))
        range_height = range_high - range_low
        curr_atr = float(atr_h1[i])
        
        if curr_atr <= 0 or range_height < (0.8 * curr_atr) or range_height > (6.0 * curr_atr):
            i += 1
            continue
            
        # 3. Manipulación (M) / Judas Swing en [i : i + 6]
        manipulation_found = False
        direction = None
        sweep_peak = None
        sweep_idx = None
        
        fvgs = find_active_fvgs_fast(df_h4, h4_idx, lookback_bars=40)
        
        if bias_bearish:
            # Ventas: Barrido por encima de range_high (BSL)
            for m_offset in range(1, 6):
                cand_idx = i + m_offset
                if cand_idx >= n_h1:
                    break
                c_high = h1_highs[cand_idx]
                c_close = h1_closes[cand_idx]
                
                if c_high > range_high:
                    fvg_mitigated = False
                    for fvg in fvgs:
                        if fvg['type'] == 'BEARISH':
                            if c_high >= fvg['bottom'] and c_high <= (fvg['top'] + (0.1 * fvg['height'])):
                                fvg_mitigated = True
                                break
                    wick_ratio = (c_high - max(h1_opens[cand_idx], c_close)) / (c_high - h1_lows[cand_idx] + 1e-9)
                    if fvg_mitigated or (wick_ratio >= 0.40):
                        direction = "SELL"
                        sweep_peak = c_high
                        sweep_idx = cand_idx
                        manipulation_found = True
                        break
                        
        elif bias_bullish:
            # Compras: Barrido por debajo de range_low (SSL)
            for m_offset in range(1, 6):
                cand_idx = i + m_offset
                if cand_idx >= n_h1:
                    break
                c_low = h1_lows[cand_idx]
                c_close = h1_closes[cand_idx]
                
                if c_low < range_low:
                    fvg_mitigated = False
                    for fvg in fvgs:
                        if fvg['type'] == 'BULLISH':
                            if c_low <= fvg['top'] and c_low >= (fvg['bottom'] - (0.1 * fvg['height'])):
                                fvg_mitigated = True
                                break
                    wick_ratio = (min(h1_opens[cand_idx], c_close) - c_low) / (h1_highs[cand_idx] - c_low + 1e-9)
                    if fvg_mitigated or (wick_ratio >= 0.40):
                        direction = "BUY"
                        sweep_peak = c_low
                        sweep_idx = cand_idx
                        manipulation_found = True
                        break

        if not manipulation_found:
            i += 1
            continue

        # 4. Confirmación Estructural en LTF: Break & Retest (MSS)
        mss_confirmed = False
        retest_idx = None
        entry_price = None
        stop_loss = None
        
        if direction == "SELL":
            local_support = min(h1_lows[sweep_idx - 3 : sweep_idx])
            break_idx = None
            for b in range(sweep_idx + 1, min(n_h1, sweep_idx + 6)):
                if h1_closes[b] < local_support:
                    break_idx = b
                    break
            if break_idx:
                for r in range(break_idx + 1, min(n_h1, break_idx + 6)):
                    if h1_highs[r] >= (local_support - (0.2 * range_height)) and h1_closes[r] <= (local_support + (0.1 * range_height)):
                        retest_idx = r
                        entry_price = local_support
                        stop_loss = sweep_peak + spread
                        mss_confirmed = True
                        break
                        
        elif direction == "BUY":
            local_resistance = max(h1_highs[sweep_idx - 3 : sweep_idx])
            break_idx = None
            for b in range(sweep_idx + 1, min(n_h1, sweep_idx + 6)):
                if h1_closes[b] > local_resistance:
                    break_idx = b
                    break
            if break_idx:
                for r in range(break_idx + 1, min(n_h1, break_idx + 6)):
                    if h1_lows[r] <= (local_resistance + (0.2 * range_height)) and h1_closes[r] >= (local_resistance - (0.1 * range_height)):
                        retest_idx = r
                        entry_price = local_resistance
                        stop_loss = sweep_peak - spread
                        mss_confirmed = True
                        break

        if not mss_confirmed or entry_price is None or stop_loss is None:
            i += 1
            continue

        risk = abs(entry_price - stop_loss)
        if risk <= 0 or risk < (1.5 * spread):
            i += 1
            continue

        # 5. Take Profit (TP1) & Validación Fibonacci (Zona Discount / Premium)
        if direction == "SELL":
            planned_reward_to_range = entry_price - range_low
            rr_natural = planned_reward_to_range / risk
            swing_low_impulse = min(h1_lows[sweep_idx : retest_idx + 1])
            fibo_50 = (sweep_peak + swing_low_impulse) / 2.0
            
            if rr_natural >= min_rr_planned and range_low < fibo_50:
                tp1_price = entry_price - (2.0 * risk)
                tp2_price_1_3 = entry_price - (3.0 * risk)
                tp2_price_1_4 = entry_price - (4.0 * risk)
            else:
                i += 1
                continue
                
        elif direction == "BUY":
            planned_reward_to_range = range_high - entry_price
            rr_natural = planned_reward_to_range / risk
            swing_high_impulse = max(h1_highs[sweep_idx : retest_idx + 1])
            fibo_50 = (sweep_peak + swing_high_impulse) / 2.0
            
            if rr_natural >= min_rr_planned and range_high > fibo_50:
                tp1_price = entry_price + (2.0 * risk)
                tp2_price_1_3 = entry_price + (3.0 * risk)
                tp2_price_1_4 = entry_price + (4.0 * risk)
            else:
                i += 1
                continue

        entry_dt = pd.to_datetime(h1_times[retest_idx], utc=True)

        setups.append({
            "symbol": symbol,
            "asset_class": ASSET_CLASSES.get(symbol, "forex"),
            "entry_time": entry_dt,
            "h1_index": retest_idx,
            "direction": direction,
            "entry_price": float(entry_price),
            "stop_loss": float(stop_loss),
            "tp1_price": float(tp1_price),
            "tp2_price_1_3": float(tp2_price_1_3),
            "tp2_price_1_4": float(tp2_price_1_4),
            "risk_points": float(risk),
            "range_height": float(range_height),
            "range_atr_ratio": float(range_height / curr_atr),
            "sweep_depth_ratio": float(abs(sweep_peak - (range_high if direction == "SELL" else range_low)) / range_height),
            "spread": float(spread),
            "spread_to_risk": float(spread / risk),
            "hour_utc": int(entry_dt.hour),
            "day_of_week": int(entry_dt.dayofweek),
        })

        i = retest_idx + 12

    return setups

def simulate_dual_position_trade(
    setup: dict,
    df_ltf: pd.DataFrame,
    target_rr_2: float,
    initial_balance: float = 10000.0,
    max_hold_bars: int = 400
) -> dict:
    """Simula la ejecución de 2 órdenes al 0.5% del capital (total 1% de riesgo):
    
    - Entrada 1 (0.5% riesgo = $50 USD): Cierra en TP1 (1:2 RR).
    - Entrada 2 (0.5% riesgo = $50 USD): Al tocar TP1, su SL se mueve a Break Even (+ spread buffer).
      Luego busca TP2 (1:3 o 1:4).
    - Si toca SL antes de TP1: Ambas órdenes pierden 0.5% (Pérdida total = -1.0% = -1.0 R).
    """
    direction = setup["direction"]
    entry_price = setup["entry_price"]
    stop_loss = setup["stop_loss"]
    tp1_price = setup["tp1_price"]
    tp2_price = setup["tp2_price_1_3"] if target_rr_2 == 3.0 else setup["tp2_price_1_4"]
    spread = setup["spread"]
    entry_time = setup["entry_time"]
    
    risk_points = setup["risk_points"]
    risk_usd_leg = initial_balance * 0.005 # 0.5% ($50)
    
    be_price = entry_price + spread if direction == "BUY" else entry_price - spread
    
    future_candles = df_ltf[df_ltf['time'] > entry_time].head(max_hold_bars)
    if future_candles.empty:
        return {
            "outcome": "NO_DATA",
            "pnl_usd": 0.0,
            "pnl_pct": 0.0,
            "r_multiple": 0.0,
            "leg1_outcome": "TIMEOUT",
            "leg2_outcome": "TIMEOUT",
            "hit_tp1": False,
            "hit_tp2": False,
            "hit_be": False,
        }

    highs = future_candles['high'].values
    lows = future_candles['low'].values
    opens = future_candles['open'].values
    closes = future_candles['close'].values
    n = len(future_candles)

    leg1_closed = False
    leg1_pnl = 0.0
    leg1_outcome = None
    
    leg2_closed = False
    leg2_pnl = 0.0
    leg2_outcome = None
    leg2_in_be = False

    for k in range(n):
        b_high = highs[k]
        b_low = lows[k]
        b_open = opens[k]
        
        # 1. Monitoreo previo a TP1
        if not leg1_closed:
            sl_hit = (b_low <= stop_loss) if direction == "BUY" else (b_high >= stop_loss)
            tp1_hit = (b_high >= tp1_price) if direction == "BUY" else (b_low <= tp1_price)
            
            if sl_hit and tp1_hit:
                if (direction == "BUY" and b_open < entry_price) or (direction == "SELL" and b_open > entry_price):
                    sl_hit, tp1_hit = True, False
                else:
                    sl_hit, tp1_hit = False, True

            if sl_hit:
                leg1_closed = True
                leg1_outcome = "SL"
                leg1_pnl = -risk_usd_leg
                
                leg2_closed = True
                leg2_outcome = "SL"
                leg2_pnl = -risk_usd_leg
                break

            elif tp1_hit:
                leg1_closed = True
                leg1_outcome = "TP1"
                leg1_pnl = risk_usd_leg * 2.0
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
                leg2_outcome = "TP2"
                leg2_pnl = risk_usd_leg * target_rr_2
                break

            elif be_sl_hit:
                leg2_closed = True
                leg2_outcome = "BREAK_EVEN" if leg2_in_be else "SL"
                leg2_pnl = 0.0 if leg2_in_be else -risk_usd_leg
                break

    if not leg1_closed:
        leg1_outcome = "TIMEOUT"
        last_close = closes[-1]
        pnl_pts = (last_close - entry_price) if direction == "BUY" else (entry_price - last_close)
        leg1_pnl = risk_usd_leg * (pnl_pts / risk_points)
        
    if not leg2_closed:
        leg2_outcome = "TIMEOUT_BE" if leg2_in_be else "TIMEOUT"
        last_close = closes[-1]
        pnl_pts = (last_close - entry_price) if direction == "BUY" else (entry_price - last_close)
        leg2_r = max(0.0, pnl_pts / risk_points) if leg2_in_be else (pnl_pts / risk_points)
        leg2_pnl = risk_usd_leg * leg2_r

    total_pnl_usd = leg1_pnl + leg2_pnl
    total_pnl_pct = (total_pnl_usd / initial_balance) * 100.0
    total_r = total_pnl_usd / (initial_balance * 0.01)

    return {
        "leg1_outcome": leg1_outcome,
        "leg2_outcome": leg2_outcome,
        "hit_tp1": (leg1_outcome == "TP1"),
        "hit_tp2": (leg2_outcome == "TP2"),
        "hit_be": (leg2_outcome == "BREAK_EVEN"),
        "total_pnl_usd": round(total_pnl_usd, 2),
        "total_pnl_pct": round(total_pnl_pct, 4),
        "total_r": round(total_r, 4),
    }

def run_full_replay():
    print("=" * 80)
    print("INICIANDO REPLAY DE 2 AÑOS - ESTRATEGIA ICT SABRI MALLE (AMD + FVG REJECTION)")
    print("GESTIÓN DUAL: 2 ENTRADAS AL 0.5% (RIESGO TOTAL 1.0%), TP1 A 1:2, TP2 A 1:3 Y 1:4")
    print("=" * 80)
    
    start_total_time = time.time()
    all_symbols = list(SPREADS.keys())
    
    all_trade_records = []
    symbol_summaries = []
    
    for symbol in all_symbols:
        t0 = time.time()
        spread = SPREADS[symbol]
        df_h1, df_ltf = load_instrument_data(symbol)
        
        if df_h1 is None:
            print(f"[-] {symbol}: No se encontraron datos.")
            continue
            
        df_h4 = build_h4_candles(df_h1)
        setups = detect_ict_sabri_malle_setups(symbol, df_h1, df_h4, spread)
        
        n_setups = len(setups)
        if n_setups == 0:
            print(f"[!] {symbol}: 0 setups encontrados.")
            continue
            
        sym_pnl_rr3 = 0.0
        sym_pnl_rr4 = 0.0
        sym_r_rr3 = 0.0
        sym_r_rr4 = 0.0
        sym_wins_tp1 = 0
        sym_wins_tp2_rr3 = 0
        sym_wins_tp2_rr4 = 0
        sym_be = 0
        sym_losses = 0
        
        for s in setups:
            res_rr3 = simulate_dual_position_trade(s, df_ltf, target_rr_2=3.0)
            res_rr4 = simulate_dual_position_trade(s, df_ltf, target_rr_2=4.0)
            
            sym_pnl_rr3 += res_rr3["total_pnl_usd"]
            sym_pnl_rr4 += res_rr4["total_pnl_usd"]
            sym_r_rr3 += res_rr3["total_r"]
            sym_r_rr4 += res_rr4["total_r"]
            
            if res_rr3["hit_tp1"]:
                sym_wins_tp1 += 1
            if res_rr3["hit_tp2"]:
                sym_wins_tp2_rr3 += 1
            if res_rr4["hit_tp2"]:
                sym_wins_tp2_rr4 += 1
            if res_rr3["hit_be"]:
                sym_be += 1
            if res_rr3["leg1_outcome"] == "SL":
                sym_losses += 1
                
            record = {
                "trade_id": f"{symbol}_{s['entry_time'].strftime('%Y%m%d_%H%M')}",
                "symbol": symbol,
                "asset_class": s["asset_class"],
                "entry_time": s["entry_time"].isoformat(),
                "direction": s["direction"],
                "entry_price": s["entry_price"],
                "stop_loss": s["stop_loss"],
                "tp1_price": s["tp1_price"],
                "tp2_price_1_3": s["tp2_price_1_3"],
                "tp2_price_1_4": s["tp2_price_1_4"],
                "risk_points": s["risk_points"],
                "range_height": s["range_height"],
                "range_atr_ratio": s["range_atr_ratio"],
                "sweep_depth_ratio": s["sweep_depth_ratio"],
                "spread": s["spread"],
                "spread_to_risk": s["spread_to_risk"],
                "hour_utc": s["hour_utc"],
                "day_of_week": s["day_of_week"],
                # Resultados bajo TP2 = 1:3
                "outcome_tp1": res_rr3["leg1_outcome"],
                "outcome_tp2_rr3": res_rr3["leg2_outcome"],
                "pnl_usd_rr3": res_rr3["total_pnl_usd"],
                "pnl_pct_rr3": res_rr3["total_pnl_pct"],
                "r_net_rr3": res_rr3["total_r"],
                "meta_label_win_rr3": 1 if res_rr3["total_r"] > 0 else 0,
                # Resultados bajo TP2 = 1:4
                "outcome_tp2_rr4": res_rr4["leg2_outcome"],
                "pnl_usd_rr4": res_rr4["total_pnl_usd"],
                "pnl_pct_rr4": res_rr4["total_pnl_pct"],
                "r_net_rr4": res_rr4["total_r"],
                "meta_label_win_rr4": 1 if res_rr4["total_r"] > 0 else 0,
            }
            all_trade_records.append(record)

        elapsed = time.time() - t0
        winrate_tp1 = (sym_wins_tp1 / n_setups) * 100.0
        winrate_tp2_rr3 = (sym_wins_tp2_rr3 / n_setups) * 100.0
        winrate_tp2_rr4 = (sym_wins_tp2_rr4 / n_setups) * 100.0
        
        symbol_summaries.append({
            "symbol": symbol,
            "asset_class": ASSET_CLASSES.get(symbol, "forex"),
            "setups": n_setups,
            "winrate_tp1_pct": round(winrate_tp1, 1),
            "winrate_tp2_rr3_pct": round(winrate_tp2_rr3, 1),
            "winrate_tp2_rr4_pct": round(winrate_tp2_rr4, 1),
            "total_r_rr3": round(sym_r_rr3, 2),
            "total_r_rr4": round(sym_r_rr4, 2),
            "pnl_usd_rr3": round(sym_pnl_rr3, 2),
            "pnl_usd_rr4": round(sym_pnl_rr4, 2),
            "expectancy_r_rr3": round(sym_r_rr3 / n_setups, 2),
            "expectancy_r_rr4": round(sym_r_rr4 / n_setups, 2),
        })
        
        print(f"[+] {symbol:<20} | Setups: {n_setups:>3} | WR TP1: {winrate_tp1:>5.1f}% | WR TP2(1:3): {winrate_tp2_rr3:>5.1f}% | R Net (1:3): {sym_r_rr3:>+6.1f}R | R Net (1:4): {sym_r_rr4:>+6.1f}R ({elapsed:.1f}s)")

    df_trades = pd.DataFrame(all_trade_records)
    df_summary = pd.DataFrame(symbol_summaries)
    
    trades_csv_path = OUTPUT_DIR / "meta_labeling_ict_sabri_malle_trades.csv"
    summary_csv_path = OUTPUT_DIR / "meta_labeling_ict_sabri_malle_summary.csv"
    
    df_trades.to_csv(trades_csv_path, index=False)
    df_summary.to_csv(summary_csv_path, index=False)
    
    print("\n" + "=" * 80)
    print("RESUMEN GLOBAL DEL REPLAY")
    print("=" * 80)
    print(f"Total oportunidades evaluadas : {len(df_trades)}")
    print(f"Dataset persistido para IA    : {trades_csv_path}")
    print(f"Resumen por activo persistido : {summary_csv_path}")
    
    tot_r_3 = df_trades["r_net_rr3"].sum()
    tot_r_4 = df_trades["r_net_rr4"].sum()
    avg_r_3 = df_trades["r_net_rr3"].mean()
    avg_r_4 = df_trades["r_net_rr4"].mean()
    wr_tp1_glob = (df_trades["outcome_tp1"] == "TP1").mean() * 100.0
    wr_tp2_3_glob = (df_trades["outcome_tp2_rr3"] == "TP2").mean() * 100.0
    wr_tp2_4_glob = (df_trades["outcome_tp2_rr4"] == "TP2").mean() * 100.0
    be_glob = (df_trades["outcome_tp2_rr3"] == "BREAK_EVEN").mean() * 100.0
    full_loss_glob = (df_trades["outcome_tp1"] == "SL").mean() * 100.0
    
    print(f"Tasa de Acierto TP1 (1:2)     : {wr_tp1_glob:.1f}%")
    print(f"Tasa de Acierto TP2 (1:3)     : {wr_tp2_3_glob:.1f}%")
    print(f"Tasa de Acierto TP2 (1:4)     : {wr_tp2_4_glob:.1f}%")
    print(f"Tasa de salidas en Break Even : {be_glob:.1f}%")
    print(f"Tasa de Pérdidas Totales (SL) : {full_loss_glob:.1f}%")
    print(f"Ganancia Neta en R (TP2 a 1:3): {tot_r_3:+.1f} R (Expectativa: {avg_r_3:+.2f} R/trade)")
    print(f"Ganancia Neta en R (TP2 a 1:4): {tot_r_4:+.1f} R (Expectativa: {avg_r_4:+.2f} R/trade)")
    print(f"Tiempo total de simulación    : {time.time() - start_total_time:.1f} segundos")
    print("=" * 80)

if __name__ == "__main__":
    run_full_replay()
