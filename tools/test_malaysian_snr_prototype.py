import sys
from pathlib import Path
from datetime import datetime, timezone, timedelta
from dataclasses import dataclass
import pandas as pd
import numpy as np
import MetaTrader5 as mt5

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from config.symbol_policy import is_direction_allowed

def fetch_data(symbol: str, days: int = 90):
    mt5.initialize()
    now = datetime.now(timezone.utc)
    start = now - timedelta(days=days)
    mt5.symbol_select(symbol, True)
    
    r_h1 = mt5.copy_rates_range(symbol, mt5.TIMEFRAME_H1, start, now)
    r_m15 = mt5.copy_rates_range(symbol, mt5.TIMEFRAME_M15, start, now)
    mt5.shutdown()
    
    if r_h1 is None or r_m15 is None:
        return None, None
        
    df_h1 = pd.DataFrame(r_h1)
    df_h1['time'] = pd.to_datetime(df_h1['time'], unit='s', utc=True)
    
    df_m15 = pd.DataFrame(r_m15)
    df_m15['time'] = pd.to_datetime(df_m15['time'], unit='s', utc=True)
    
    return df_h1, df_m15

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
        return 4.0 # Mercado cerrado / illiquid gap
    # Rollover nocturno (21:00 a 23:00 UTC)
    if 21.0 <= t_float < 23.0:
        return 3.0
    # Killzones Londres (07:00-10:00 UTC) y NY (12:00-16:00 UTC)
    if (7.0 <= t_float <= 10.0) or (12.0 <= t_float <= 16.0):
        return 1.0
    # Fuera de killzone (Asia / descanso)
    return 1.5

def detect_malaysian_snr_signals(df_h1: pd.DataFrame, df_m15: pd.DataFrame, symbol: str, base_spread: float):
    is_synth = any(k in symbol.lower() for k in ["index", "volatility", "boom", "crash", "step", "jump"])
    df_h1 = df_h1.copy()
    df_m15 = df_m15.copy()
    df_h1["atr"] = compute_atr(df_h1, 14)
    df_h1["adx"] = compute_adx(df_h1, 14)
    
    # Identificar patrones A/V y Breaks en H1
    h1_levels = [] # list of dicts: type, level, break_level, time, idx
    for i in range(2, len(df_h1) - 1):
        prev = df_h1.iloc[i-1]
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
                
    signals = []
    # Evaluar interacciones con niveles pasados (lookback de hasta 50 velas H1)
    for k in range(15, len(df_h1)):
        candle = df_h1.iloc[k]
        c_time = candle["time"]
        c_open = candle["open"]
        c_close = candle["close"]
        c_high = candle["high"]
        c_low = candle["low"]
        c_span = c_high - c_low
        if c_span <= 0:
            continue
            
        c_atr = candle["atr"] if not pd.isna(candle["atr"]) else c_span
        c_adx = candle["adx"] if not pd.isna(candle["adx"]) else 20.0
        
        # Revisar niveles activos recientes (no más de 40 barras de antigüedad)
        recent_levels = [lvl for lvl in h1_levels if 2 < (k - lvl["idx"]) <= 40]
        for lvl in recent_levels:
            lvl_price = lvl["level"]
            break_price = lvl["break_level"]
            lvl_type = lvl["type"]
            
            # 1. EVALUAR RESISTENCIA (Patrón A)
            if lvl_type == "A_RESISTANCE":
                # Escenario 1: Ruptura Clásica (FRESH) -> BUY
                # Cierre claro por encima de la resistencia con cuerpo fuerte y poca mecha superior
                body = c_close - c_open
                upper_wick = c_high - c_close
                if c_close > lvl_price and body / c_span >= 0.50 and upper_wick / c_span <= 0.30:
                    if is_direction_allowed(symbol, "BUY"):
                        signals.append({
                            "symbol": symbol,
                            "scenario": "ESC_1_CONTINUATION",
                            "direction": "BUY",
                            "time": c_time,
                            "entry_price": break_price,
                            "stop_loss": c_low - (0.2 * c_atr),
                            "momentum_adx": c_adx,
                            "body_ratio": body / c_span,
                            "ref_level": lvl_price,
                        })
                        break
                # Escenario 2: SNR Clásico (NO FRESH / Manipulación) -> SELL
                # Mecha traspasa nivel pero cierra por debajo
                rejection_wick = c_high - max(c_open, c_close)
                if c_high > lvl_price and c_close <= lvl_price and rejection_wick / c_span >= 0.35:
                    if is_direction_allowed(symbol, "SELL"):
                        signals.append({
                            "symbol": symbol,
                            "scenario": "ESC_2_REVERSAL",
                            "direction": "SELL",
                            "time": c_time,
                            "entry_price": c_close,
                            "stop_loss": c_high + (0.2 * c_atr),
                            "momentum_adx": c_adx,
                            "body_ratio": abs(c_close - c_open) / c_span,
                            "ref_level": lvl_price,
                        })
                        break

            # 2. EVALUAR SOPORTE (Patrón V)
            elif lvl_type == "V_SUPPORT":
                # Escenario 1: Ruptura Clásica (FRESH) -> SELL
                body = c_open - c_close
                lower_wick = c_close - c_low
                if c_close < lvl_price and body / c_span >= 0.50 and lower_wick / c_span <= 0.30:
                    if is_direction_allowed(symbol, "SELL"):
                        signals.append({
                            "symbol": symbol,
                            "scenario": "ESC_1_CONTINUATION",
                            "direction": "SELL",
                            "time": c_time,
                            "entry_price": break_price,
                            "stop_loss": c_high + (0.2 * c_atr),
                            "momentum_adx": c_adx,
                            "body_ratio": body / c_span,
                            "ref_level": lvl_price,
                        })
                        break
                # Escenario 2: SNR Clásico (NO FRESH / Manipulación) -> BUY
                rejection_wick = min(c_open, c_close) - c_low
                if c_low < lvl_price and c_close >= lvl_price and rejection_wick / c_span >= 0.35:
                    if is_direction_allowed(symbol, "BUY"):
                        signals.append({
                            "symbol": symbol,
                            "scenario": "ESC_2_REVERSAL",
                            "direction": "BUY",
                            "time": c_time,
                            "entry_price": c_close,
                            "stop_loss": c_low - (0.2 * c_atr),
                            "momentum_adx": c_adx,
                            "body_ratio": abs(c_close - c_open) / c_span,
                            "ref_level": lvl_price,
                        })
                        break
                        
    # Añadir Escenario 3 (Fractalidad rápida), Escenario 4 (Falla / Stop & Reverse) y Escenario 5 (FVG)
    # Escenario 5: FVG Imbalances de 3 velas
    for i in range(3, len(df_h1) - 2):
        c0, c1, c2 = df_h1.iloc[i-2], df_h1.iloc[i-1], df_h1.iloc[i]
        # Bullish FVG
        if c2["low"] > c0["high"]:
            gap_top = c2["low"]
            gap_bot = c0["high"]
            # Probar interacción en siguientes velas
            for f in range(i+1, min(i+15, len(df_h1))):
                cf = df_h1.iloc[f]
                # Reacción No Fresh dentro del FVG (rebote)
                if cf["low"] <= gap_top and cf["close"] > gap_top:
                    if is_direction_allowed(symbol, "BUY"):
                        signals.append({
                            "symbol": symbol,
                            "scenario": "ESC_5_FVG_REBOUND",
                            "direction": "BUY",
                            "time": cf["time"],
                            "entry_price": cf["close"],
                            "stop_loss": gap_bot - (0.1 * (gap_top - gap_bot)),
                            "momentum_adx": cf["adx"] if not pd.isna(cf["adx"]) else 20.0,
                            "body_ratio": 0.6,
                            "ref_level": gap_top,
                        })
                    break
                # Perforación Fresh del FVG (continuación a través del gap)
                elif cf["close"] < gap_bot:
                    if is_direction_allowed(symbol, "SELL"):
                        signals.append({
                            "symbol": symbol,
                            "scenario": "ESC_5_FVG_PIERCE",
                            "direction": "SELL",
                            "time": cf["time"],
                            "entry_price": gap_bot,
                            "stop_loss": gap_top,
                            "momentum_adx": cf["adx"] if not pd.isna(cf["adx"]) else 20.0,
                            "body_ratio": 0.7,
                            "ref_level": gap_bot,
                        })
                    break
        # Bearish FVG
        elif c2["high"] < c0["low"]:
            gap_top = c0["low"]
            gap_bot = c2["high"]
            for f in range(i+1, min(i+15, len(df_h1))):
                cf = df_h1.iloc[f]
                # Reacción No Fresh dentro del FVG (rebote)
                if cf["high"] >= gap_bot and cf["close"] < gap_bot:
                    if is_direction_allowed(symbol, "SELL"):
                        signals.append({
                            "symbol": symbol,
                            "scenario": "ESC_5_FVG_REBOUND",
                            "direction": "SELL",
                            "time": cf["time"],
                            "entry_price": cf["close"],
                            "stop_loss": gap_top + (0.1 * (gap_top - gap_bot)),
                            "momentum_adx": cf["adx"] if not pd.isna(cf["adx"]) else 20.0,
                            "body_ratio": 0.6,
                            "ref_level": gap_bot,
                        })
                    break
                # Perforación Fresh
                elif cf["close"] > gap_top:
                    if is_direction_allowed(symbol, "BUY"):
                        signals.append({
                            "symbol": symbol,
                            "scenario": "ESC_5_FVG_PIERCE",
                            "direction": "BUY",
                            "time": cf["time"],
                            "entry_price": gap_top,
                            "stop_loss": gap_bot,
                            "momentum_adx": cf["adx"] if not pd.isna(cf["adx"]) else 20.0,
                            "body_ratio": 0.7,
                            "ref_level": gap_top,
                        })
                    break
                    
    # Filtrar señales duplicadas muy cercanas (mínimo 4 velas M15 entre señales)
    signals = sorted(signals, key=lambda s: s["time"])
    filtered_signals = []
    last_time = None
    for s in signals:
        if last_time is None or (s["time"] - last_time) >= timedelta(hours=2):
            filtered_signals.append(s)
            last_time = s["time"]
            
    return filtered_signals

def test_run():
    print("Iniciando prueba en EURUSD y Volatility 75 Index...")
    df_h1, df_m15 = fetch_data("EURUSD", days=60)
    if df_h1 is not None:
        sigs = detect_malaysian_snr_signals(df_h1, df_m15, "EURUSD", 0.00010)
        print(f"EURUSD: H1={len(df_h1)} barras -> {len(sigs)} señales Malaysian SNR detectadas.")
        if sigs:
            print("  Muestra de señal:", sigs[0])
            
    df_h1_v, df_m15_v = fetch_data("Volatility 75 Index", days=60)
    if df_h1_v is not None:
        sigs_v = detect_malaysian_snr_signals(df_h1_v, df_m15_v, "Volatility 75 Index", 2.0)
        print(f"Volatility 75 Index: H1={len(df_h1_v)} barras -> {len(sigs_v)} señales Malaysian SNR detectadas.")
        if sigs_v:
            print("  Muestra de señal:", sigs_v[0])

if __name__ == "__main__":
    test_run()

