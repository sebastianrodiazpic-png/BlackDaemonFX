"""
Replay Histórico Cuantitativo de 2 Años con Reglas Optimizadas SMC:
- Multi-timeframe: H1 (Descuento/Premium 50% + FVG) -> M5 (Barrida Liquidez + CHoCH por cuerpo con desplazamiento).
- Riesgo: 1.0% total por oportunidad, dividido en 2 entradas al 50% (0.5% Leg 1 + 0.5% Leg 2).
- Gestión:
  * Leg 1 (0.5%): Cierra en TP1 (Mínimo 1:2.0 R:R).
  * Leg 2 (0.5%): Busca TP2 (1:3.5 R:R). Al tocar TP1, mueve SL a Break-Even neto considerando el spread.
- Mercados Tradicionales (Forex / Gold):
  * Respeta Killzones de Londres y NY.
  * Respeta cierres de fin de semana (Viernes 16:00 NY).
  * Respeta ventana de Rollover NY -> Asia (16:45 - 17:30 NY) con expansión de spread de 4x y bloqueo de entradas.
  * Filtro de noticias de alto impacto (08:30 NY y 14:00 NY).
- Índices Sintéticos (Volatility, Step, Jump, Boom, Crash):
  * Operación 24/7 continua sin pausas de sesión ni rollover.
  * Asimetría direccional respetada: Boom solo BUY, Crash solo SELL.
- Preparación para IA:
  * Extracción de meta-características por trade compatible con el esquema de Meta-Labeling.
  * Exportación de dataset listo para entrenamiento y re-calibración en storage/analysis/.
"""

import sys
import os
import math
import json
from pathlib import Path
from datetime import datetime, timezone, timedelta
from zoneinfo import ZoneInfo
import numpy as np
import pandas as pd
import MetaTrader5 as mt5

NY_TZ = ZoneInfo("America/New_York")
UTC = timezone.utc

# Costes y parámetros por instrumento
INSTRUMENT_SPECS = {
    # Forex
    "EURUSD": {"category": "forex", "spread": 0.00012, "pip": 0.0001, "dir_policy": "BOTH"},
    "GBPUSD": {"category": "forex", "spread": 0.00018, "pip": 0.0001, "dir_policy": "BOTH"},
    "USDJPY": {"category": "forex", "spread": 0.015,   "pip": 0.01,   "dir_policy": "BOTH"},
    "USDCHF": {"category": "forex", "spread": 0.00015, "pip": 0.0001, "dir_policy": "BOTH"},
    # Metales
    "XAUUSD": {"category": "gold",  "spread": 0.59,    "pip": 0.1,    "dir_policy": "BOTH"},
    # Sintéticos Deriv
    "Step Index":          {"category": "step",       "spread": 0.10, "pip": 0.1, "dir_policy": "BOTH"},
    "Volatility 75 Index": {"category": "volatility", "spread": 1.50, "pip": 0.1, "dir_policy": "BOTH"},
    "Volatility 100 Index":{"category": "volatility", "spread": 2.00, "pip": 0.1, "dir_policy": "BOTH"},
    "Jump 50 Index":       {"category": "jump",       "spread": 0.50, "pip": 0.1, "dir_policy": "BOTH"},
    "Boom 1000 Index":     {"category": "boom",       "spread": 0.80, "pip": 0.1, "dir_policy": "BUY_ONLY"},
    "Crash 1000 Index":    {"category": "crash",      "spread": 0.80, "pip": 0.1, "dir_policy": "SELL_ONLY"},
}

def is_in_killzone(dt_ny):
    hour = dt_ny.hour
    minute = dt_ny.minute
    t_min = hour * 60 + minute
    london_kz = (2 * 60 <= t_min < 5 * 60)
    ny_kz = (7 * 60 <= t_min < 11 * 60)
    return london_kz, ny_kz

def is_market_close_or_rollover(dt_ny):
    weekday = dt_ny.weekday()
    hour = dt_ny.hour
    minute = dt_ny.minute
    t_min = hour * 60 + minute
    # Fin de semana
    if (weekday == 4 and t_min >= 16 * 60) or weekday == 5 or (weekday == 6 and t_min < 17 * 60):
        return True, "WEEKEND_CLOSE"
    # Rollover diario New York -> Asia
    if 16 * 60 + 45 <= t_min < 17 * 60 + 30:
        return True, "DAILY_ROLLOVER"
    return False, "OPEN"

def is_high_impact_news_window(dt_ny):
    hour = dt_ny.hour
    minute = dt_ny.minute
    t_min = hour * 60 + minute
    weekday = dt_ny.weekday()
    # 08:30 NY macro window
    if 8 * 60 <= t_min <= 9 * 60:
        return True, "NEWS_0830_MACRO"
    # 10:00 NY ISM/Consumer window
    if 9 * 60 + 45 <= t_min <= 10 * 60 + 20:
        return True, "NEWS_1000_ISM"
    # 14:00 FOMC (miércoles)
    if weekday == 2 and (13 * 60 + 30 <= t_min <= 14 * 60 + 45):
        return True, "NEWS_1400_FOMC"
    return False, "NO_NEWS"

def compute_atr(high, low, close, period=14):
    tr = np.maximum(high[1:] - low[1:], np.maximum(np.abs(high[1:] - close[:-1]), np.abs(low[1:] - close[:-1])))
    atr = np.zeros(len(close))
    if len(tr) >= period:
        atr[period] = np.mean(tr[:period])
        for k in range(period + 1, len(close)):
            atr[k] = (atr[k-1] * (period - 1) + tr[k-1]) / period
    return atr

def compute_adx(high, low, close, period=14):
    n = len(close)
    if n < period * 2:
        return np.full(n, 20.0)
    up_move = high[1:] - high[:-1]
    down_move = low[:-1] - low[1:]
    plus_dm = np.where((up_move > down_move) & (up_move > 0), up_move, 0.0)
    minus_dm = np.where((down_move > up_move) & (down_move > 0), down_move, 0.0)
    tr = np.maximum(high[1:] - low[1:], np.maximum(np.abs(high[1:] - close[:-1]), np.abs(low[1:] - close[:-1])))
    
    # Smooth
    atr = np.zeros(n)
    p_di = np.zeros(n)
    m_di = np.zeros(n)
    adx = np.zeros(n)
    
    atr[period] = np.sum(tr[:period])
    p_di[period] = np.sum(plus_dm[:period])
    m_di[period] = np.sum(minus_dm[:period])
    
    for i in range(period + 1, n):
        atr[i] = atr[i-1] - (atr[i-1] / period) + tr[i-1]
        p_di[i] = p_di[i-1] - (p_di[i-1] / period) + plus_dm[i-1]
        m_di[i] = m_di[i-1] - (m_di[i-1] / period) + minus_dm[i-1]
        
    plus_di_pct = np.where(atr > 0, 100.0 * p_di / atr, 0.0)
    minus_di_pct = np.where(atr > 0, 100.0 * m_di / atr, 0.0)
    
    sum_di = plus_di_pct + minus_di_pct
    dx = np.where(sum_di > 0, 100.0 * np.abs(plus_di_pct - minus_di_pct) / sum_di, 0.0)
    
    start_adx = period * 2
    if n > start_adx:
        adx[start_adx] = np.mean(dx[period:start_adx])
        for i in range(start_adx + 1, n):
            adx[i] = (adx[i-1] * (period - 1) + dx[i]) / period
    return np.where(adx > 0, adx, 22.0)

def load_data(symbol, spec):
    """Carga los datos M5 y H1 desde MT5 si es sintético o desde CSV/MT5 si es Forex/Gold."""
    clean = symbol.replace(" ", "_")
    cat = spec["category"]
    
    # Intentar CSV primero si existe
    csv_dir = "data/forex_historical" if cat == "forex" else "data/historical"
    m5_p = Path(csv_dir) / f"{clean}_M5.csv"
    h1_p = Path(csv_dir) / f"{clean}_H1.csv"
    
    if m5_p.exists() and h1_p.exists():
        print(f"  [CSV] Cargando {symbol} desde archivos locales...")
        df_m5 = pd.read_csv(m5_p)
        df_h1 = pd.read_csv(h1_p)
        df_m5['time'] = pd.to_datetime(df_m5['time'], utc=True)
        df_h1['time'] = pd.to_datetime(df_h1['time'], utc=True)
        return df_m5.sort_values('time').reset_index(drop=True), df_h1.sort_values('time').reset_index(drop=True)
        
    # Si no existe en CSV, intentar descargar de MT5
    if mt5.initialize():
        print(f"  [MT5] Descargando histórico vivo para {symbol}...")
        mt5.symbol_select(symbol, True)
        rates_m5 = None
        for try_cnt in [80000, 70000, 50000, 30000]:
            rates_m5 = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_M5, 0, try_cnt)
            if rates_m5 is not None and len(rates_m5) > 1000:
                break
        rates_h1 = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_H1, 0, 15000)
        if rates_m5 is not None and rates_h1 is not None and len(rates_m5) > 1000:
            df_m5 = pd.DataFrame(rates_m5)
            df_h1 = pd.DataFrame(rates_h1)
            df_m5['time'] = pd.to_datetime(df_m5['time'], unit='s', utc=True)
            df_h1['time'] = pd.to_datetime(df_h1['time'], unit='s', utc=True)
            # Guardar en data/historical para futuras ejecuciones
            Path("data/historical").mkdir(parents=True, exist_ok=True)
            df_m5.to_csv(f"data/historical/{clean}_M5.csv", index=False)
            df_h1.to_csv(f"data/historical/{clean}_H1.csv", index=False)
            print(f"  [MT5] Descargados {len(df_m5)} barras M5 y {len(df_h1)} barras H1 guardados en cache.")
            return df_m5.sort_values('time').reset_index(drop=True), df_h1.sort_values('time').reset_index(drop=True)
            
    print(f"  [ERROR] No se pudieron cargar datos para {symbol}")
    return None, None


def simulate_instrument_smc(symbol, spec, df_m5, df_h1):
    category = spec["category"]
    base_spread = spec["spread"]
    pip_size = spec["pip"]
    dir_policy = spec["dir_policy"]
    is_synthetic = (category in ["volatility", "step", "jump", "boom", "crash"])
    
    m5_times = df_m5['time'].values
    h1_times = df_h1['time'].values
    
    m5_high = df_m5['high'].values
    m5_low = df_m5['low'].values
    m5_close = df_m5['close'].values
    m5_open = df_m5['open'].values
    
    h1_high = df_h1['high'].values
    h1_low = df_h1['low'].values
    h1_close = df_h1['close'].values
    
    # Pre-calcular ADX y ATR en M5 para el modelo de IA
    m5_adx = compute_adx(m5_high, m5_low, m5_close, period=14)
    m5_atr = compute_atr(m5_high, m5_low, m5_close, period=14)
    
    # Pre-detectar FVGs en H1
    bull_fvgs = [] # (bar_idx, bottom, top)
    bear_fvgs = []
    for j in range(2, len(df_h1)):
        if h1_low[j] > h1_high[j-2]:
            bull_fvgs.append((j, h1_high[j-2], h1_low[j]))
        if h1_high[j] < h1_low[j-2]:
            bear_fvgs.append((j, h1_high[j], h1_low[j-2]))
            
    trades = []
    active_trades = []
    last_entry_time = None
    min_cooldown = timedelta(hours=2)
    
    TP1_RR = 2.0  # Mínimo 1:2.0
    TP2_RR = 3.5  # Objetivo extendido
    
    for i in range(25, len(df_m5)):
        cur_t_dt = pd.Timestamp(m5_times[i]).to_pydatetime()
        cur_t_ny = cur_t_dt.astimezone(NY_TZ)
        
        cur_h = m5_high[i]
        cur_l = m5_low[i]
        cur_c = m5_close[i]
        cur_o = m5_open[i]
        
        # Determinar spread dinámico actual:
        # En Forex/Gold, durante rollover (16:45 a 17:30 NY), spread se expande 4x
        cur_spread = base_spread
        is_close, close_reason = (False, "OPEN")
        if not is_synthetic:
            is_close, close_reason = is_market_close_or_rollover(cur_t_ny)
            if is_close and close_reason == "DAILY_ROLLOVER":
                cur_spread = base_spread * 4.0
                
        # 1. Gestionar trades activos
        remaining_trades = []
        for tr in active_trades:
            direction = tr["direction"]
            sl = tr["sl"]
            tp1 = tr["tp1"]
            tp2 = tr["tp2"]
            
            if direction == "BUY":
                # Comprobar SL
                if cur_l <= sl:
                    if not tr["leg1_closed"]:
                        tr["leg1_pnl_r"] = -1.0
                        tr["leg1_closed"] = True
                        tr["leg1_exit_time"] = cur_t_dt
                    if not tr["leg2_closed"]:
                        # Si leg 2 estaba en break-even
                        tr["leg2_pnl_r"] = 0.0 if tr["leg2_be_active"] else -1.0
                        tr["leg2_closed"] = True
                        tr["leg2_exit_time"] = cur_t_dt
                    trades.append(tr)
                    continue
                    
                # Comprobar TP1 (1:2.0)
                if not tr["leg1_closed"] and cur_h >= tp1:
                    tr["leg1_pnl_r"] = TP1_RR # +2.0R en esta pierna (+1.0% de cuenta)
                    tr["leg1_closed"] = True
                    tr["leg1_exit_time"] = cur_t_dt
                    # Mover Leg 2 a Break-Even neto protegido con spread!
                    tr["sl"] = tr["entry_price"] + base_spread
                    tr["leg2_be_active"] = True
                    
                # Comprobar TP2 (1:3.5)
                if not tr["leg2_closed"] and cur_h >= tp2:
                    tr["leg2_pnl_r"] = TP2_RR
                    tr["leg2_closed"] = True
                    tr["leg2_exit_time"] = cur_t_dt
                    
            elif direction == "SELL":
                # En SELL, el precio que toca SL es el Ask (Bid + spread actual)
                ask_h = cur_h + cur_spread
                ask_l = cur_l + cur_spread
                
                # Comprobar SL
                if ask_h >= sl:
                    if not tr["leg1_closed"]:
                        tr["leg1_pnl_r"] = -1.0
                        tr["leg1_closed"] = True
                        tr["leg1_exit_time"] = cur_t_dt
                    if not tr["leg2_closed"]:
                        tr["leg2_pnl_r"] = 0.0 if tr["leg2_be_active"] else -1.0
                        tr["leg2_closed"] = True
                        tr["leg2_exit_time"] = cur_t_dt
                    trades.append(tr)
                    continue
                    
                # Comprobar TP1 (1:2.0)
                if not tr["leg1_closed"] and ask_l <= tp1:
                    tr["leg1_pnl_r"] = TP1_RR
                    tr["leg1_closed"] = True
                    tr["leg1_exit_time"] = cur_t_dt
                    # Break-Even en Sell: Entry - spread
                    tr["sl"] = tr["entry_price"] - base_spread
                    tr["leg2_be_active"] = True
                    
                # Comprobar TP2 (1:3.5)
                if not tr["leg2_closed"] and ask_l <= tp2:
                    tr["leg2_pnl_r"] = TP2_RR
                    tr["leg2_closed"] = True
                    tr["leg2_exit_time"] = cur_t_dt
                    
            # Si ambas piernas cerradas
            if tr["leg1_closed"] and tr["leg2_closed"]:
                trades.append(tr)
            else:
                # Si llega el cierre de viernes en Forex/Gold, forzar cierre a mercado
                if not is_synthetic and is_close and close_reason == "WEEKEND_CLOSE":
                    exit_p = cur_c if direction == "BUY" else (cur_c + cur_spread)
                    risk_d = abs(tr["entry_price"] - tr["orig_sl"])
                    pnl_r = ((exit_p - tr["entry_price"]) / risk_d) if direction == "BUY" else ((tr["entry_price"] - exit_p) / risk_d)
                    if not tr["leg1_closed"]:
                        tr["leg1_pnl_r"] = pnl_r
                        tr["leg1_closed"] = True
                        tr["leg1_exit_time"] = cur_t_dt
                    if not tr["leg2_closed"]:
                        tr["leg2_pnl_r"] = pnl_r
                        tr["leg2_closed"] = True
                        tr["leg2_exit_time"] = cur_t_dt
                    tr["exit_reason"] = "WEEKEND_FORCED_CLOSE"
                    trades.append(tr)
                else:
                    remaining_trades.append(tr)
                    
        active_trades = remaining_trades
        
        # Max 1 trade activo simultáneo por símbolo
        if len(active_trades) >= 1:
            continue
            
        # Cooldown de 2 horas entre entradas
        if last_entry_time and (cur_t_dt - last_entry_time) < min_cooldown:
            continue
            
        # 2. FILTROS DE MERCADO:
        if not is_synthetic:
            # En Forex/Gold:
            # A) Bloquear rollover y cierre de fin de semana
            if is_close:
                continue
            # B) Exigir Killzones (Londres o NY)
            is_london, is_ny = is_in_killzone(cur_t_ny)
            if not (is_london or is_ny):
                continue
            # C) Bloquear noticias de alto impacto
            has_news, _ = is_high_impact_news_window(cur_t_ny)
            if has_news:
                continue
        # Si es sintético: Mercado 24/7 continuo, SIN filtros de horario/sesión
        
        # 3. CONTEXTO H1 (Sin lookahead bias):
        t_val = m5_times[i]
        h1_idx = np.searchsorted(h1_times, t_val, side='left')
        if h1_idx < 25:
            continue
            
        # Rango H1 últimas 24 velas
        h1_high_24 = np.max(h1_high[h1_idx - 24 : h1_idx])
        h1_low_24 = np.min(h1_low[h1_idx - 24 : h1_idx])
        h1_mid = (h1_high_24 + h1_low_24) / 2.0
        
        # FVGs de H1 activos
        recent_bull_fvgs = [f for f in bull_fvgs if (h1_idx - 24 <= f[0] < h1_idx)]
        recent_bear_fvgs = [f for f in bear_fvgs if (h1_idx - 24 <= f[0] < h1_idx)]
        
        inside_bull = any(f[1] <= cur_l <= f[2] or f[1] <= cur_c <= f[2] for f in recent_bull_fvgs)
        inside_bear = any(f[1] <= cur_h <= f[2] or f[1] <= cur_c <= f[2] for f in recent_bear_fvgs)
        
        if not (inside_bull or inside_bear):
            continue
            
        # Filtro Descuento / Premium (50% de Fibonacci del swing H1)
        if inside_bull and cur_c > h1_mid: # Prohibido comprar en Premium
            inside_bull = False
        if inside_bear and cur_c < h1_mid: # Prohibido vender en Descuento
            inside_bear = False
            
        # Restricción de dirección por activo
        if dir_policy == "BUY_ONLY":
            inside_bear = False
        elif dir_policy == "SELL_ONLY":
            inside_bull = False
            
        if not (inside_bull or inside_bear):
            continue
            
        # 4. MICROESTRUCTURA M5 (Barrida + CHoCH por cuerpo con desplazamiento):
        sub_h = m5_high[i-15 : i]
        sub_l = m5_low[i-15 : i]
        local_swing_low = np.min(sub_l[:-2])
        local_swing_high = np.max(sub_h[:-2])
        
        candle_range = cur_h - cur_l
        candle_body = abs(cur_c - cur_o)
        displacement_ok = (candle_body / candle_range >= 0.50) if candle_range > 0 else False
        
        # A) Setup BUY:
        if inside_bull and displacement_ok:
            # Barrida: alguna de las últimas 3 velas perforó el mínimo previo y rebotó
            swept = any(m5_low[i-k] < local_swing_low and m5_close[i-k] > local_swing_low for k in range(1, 4))
            # CHoCH: vela actual rompe por cuerpo el máximo local intermedio
            choch_level = np.max(sub_h[-5:-1])
            choch = (cur_c > choch_level and m5_close[i-1] <= choch_level)
            
            if swept and choch:
                sweep_low = min(m5_low[i-k] for k in range(1, 5))
                sl_price = sweep_low - (base_spread * 1.5)
                entry_price = cur_c + base_spread # Ask
                sl_distance = entry_price - sl_price
                
                # Spread Guard: Spread no debe exceder el 20% del SL (mínimo 6 pips en EURUSD)
                if sl_distance > 0 and (base_spread / sl_distance) <= 0.20:
                    trade = {
                        "symbol": symbol,
                        "category": category,
                        "direction": "BUY",
                        "entry_time": cur_t_dt,
                        "entry_price": entry_price,
                        "sl": sl_price,
                        "orig_sl": sl_price,
                        "tp1": entry_price + (sl_distance * TP1_RR),
                        "tp2": entry_price + (sl_distance * TP2_RR),
                        "sl_dist": sl_distance,
                        "risk_percent": 1.0,
                        "leg1_closed": False,
                        "leg2_closed": False,
                        "leg2_be_active": False,
                        "leg1_pnl_r": 0.0,
                        "leg2_pnl_r": 0.0,
                        "adx": m5_adx[i],
                        "atr_ratio": (m5_atr[i] / (sl_distance + 1e-9)),
                        "spread_to_sl_ratio": base_spread / sl_distance,
                        "trade_score": 85.0 if swept and displacement_ok else 75.0,
                        "exit_reason": "NORMAL"
                    }
                    active_trades.append(trade)
                    last_entry_time = cur_t_dt
                    continue
                    
        # B) Setup SELL:
        if inside_bear and displacement_ok:
            swept = any(m5_high[i-k] > local_swing_high and m5_close[i-k] < local_swing_high for k in range(1, 4))
            choch_level = np.min(sub_l[-5:-1])
            choch = (cur_c < choch_level and any(m5_close[i-k] >= choch_level for k in range(1, 3)))
            
            if swept and choch:
                sweep_high = max(m5_high[i-k] for k in range(1, 5))
                sl_price = sweep_high + (base_spread * 2.5)
                entry_price = cur_c # Bid
                sl_distance = sl_price - entry_price
                
                if sl_distance > 0 and (base_spread / sl_distance) <= 0.20:
                    trade = {
                        "symbol": symbol,
                        "category": category,
                        "direction": "SELL",
                        "entry_time": cur_t_dt,
                        "entry_price": entry_price,
                        "sl": sl_price,
                        "orig_sl": sl_price,
                        "tp1": entry_price - (sl_distance * TP1_RR),
                        "tp2": entry_price - (sl_distance * TP2_RR),
                        "sl_dist": sl_distance,
                        "risk_percent": 1.0,
                        "leg1_closed": False,
                        "leg2_closed": False,
                        "leg2_be_active": False,
                        "leg1_pnl_r": 0.0,
                        "leg2_pnl_r": 0.0,
                        "adx": m5_adx[i],
                        "atr_ratio": (m5_atr[i] / (sl_distance + 1e-9)),
                        "spread_to_sl_ratio": base_spread / sl_distance,
                        "trade_score": 85.0 if swept and displacement_ok else 75.0,
                        "exit_reason": "NORMAL"
                    }
                    active_trades.append(trade)
                    last_entry_time = cur_t_dt
                    continue
                    
    return trades

def compute_detailed_metrics(trades_list, initial_balance=10000.0):
    if not trades_list:
        return {
            "trades": 0, "win_rate_tp1": 0, "win_rate_full": 0, "be_rate": 0,
            "profit_factor": 0, "net_return_pct": 0, "max_drawdown_pct": 0,
            "sharpe_ratio": 0, "expectancy_r": 0, "avg_win_r": 0, "avg_loss_r": 0
        }
    df = pd.DataFrame(trades_list)
    # Cada trade arriesga 1% total: 0.5% en pierna 1 y 0.5% en pierna 2
    # PnL total en R respecto al 1% de la cuenta = (leg1 * 0.5) + (leg2 * 0.5)
    df['total_pnl_r'] = (df['leg1_pnl_r'] * 0.5) + (df['leg2_pnl_r'] * 0.5)
    
    total = len(df)
    tp1_hits = df[df['leg1_pnl_r'] > 0]
    tp2_hits = df[df['leg2_pnl_r'] > 0]
    be_hits = df[(df['leg1_pnl_r'] > 0) & (df['leg2_pnl_r'] == 0.0)]
    both_loss = df[(df['leg1_pnl_r'] < 0) & (df['leg2_pnl_r'] < 0)]
    
    wr_tp1 = (len(tp1_hits) / total) * 100
    wr_full = (len(tp2_hits) / total) * 100
    be_rate = (len(be_hits) / total) * 100
    
    winning = df[df['total_pnl_r'] > 0]
    losing = df[df['total_pnl_r'] < 0]
    
    gw = winning['total_pnl_r'].sum()
    gl = abs(losing['total_pnl_r'].sum())
    pf = (gw / gl) if gl > 0 else 999.0
    
    balance = initial_balance
    peak = balance
    dds = []
    for r in df['total_pnl_r']:
        balance += balance * (r * 0.01) # 1 R = 1%
        if balance > peak:
            peak = balance
        dds.append((peak - balance) / peak * 100)
        
    net_return_pct = (balance - initial_balance) / initial_balance * 100
    max_dd = max(dds) if dds else 0.0
    
    exp_r = df['total_pnl_r'].mean()
    sharpe = (df['total_pnl_r'].mean() / df['total_pnl_r'].std() * math.sqrt(252)) if df['total_pnl_r'].std() > 0 else 0
    
    return {
        "trades": total,
        "win_rate_tp1": wr_tp1,
        "win_rate_full": wr_full,
        "be_rate": be_rate,
        "profit_factor": pf,
        "net_return_pct": net_return_pct,
        "max_drawdown_pct": max_dd,
        "sharpe_ratio": sharpe,
        "expectancy_r": exp_r,
        "avg_win_r": winning['total_pnl_r'].mean() if len(winning) > 0 else 0,
        "avg_loss_r": losing['total_pnl_r'].mean() if len(losing) > 0 else 0
    }

def main():
    print("=" * 85)
    print("REPLAY HISTÓRICO AVANZADO 2 AÑOS (SMC OPTIMIZADO + GESTIÓN DUAL 1:2 / 1:3.5)")
    print("Reglas: H1 Discount/Premium + M5 Sweep & CHoCH Displacement")
    print("Gestión: 1% Total (0.5% Leg 1 TP1 1:2.0 + 0.5% Leg 2 TP2 1:3.5 con BE+Spread)")
    print("Forex/Gold: Killzones, News Filter, Rollover 4x Spread | Sintéticos: 24/7 Continuo")
    print("=" * 85)
    
    out_dir = Path("storage/analysis")
    out_dir.mkdir(parents=True, exist_ok=True)
    
    all_trades = []
    results_by_asset = {}
    
    for symbol, spec in INSTRUMENT_SPECS.items():
        print(f"\n--- Procesando: {symbol} (Categoría: {spec['category'].upper()}) ---")
        df_m5, df_h1 = load_data(symbol, spec)
        if df_m5 is None or df_h1 is None:
            continue
            
        sym_trades = simulate_instrument_smc(symbol, spec, df_m5, df_h1)
        all_trades.extend(sym_trades)
        metrics = compute_detailed_metrics(sym_trades)
        results_by_asset[symbol] = {
            "category": spec["category"],
            "metrics": metrics,
            "trades_count": len(sym_trades)
        }
        
        print(f"  Trades: {metrics['trades']:3} | WR TP1: {metrics['win_rate_tp1']:4.1f}% | WR TP2: {metrics['win_rate_full']:4.1f}% | BE Rate: {metrics['be_rate']:4.1f}%")
        print(f"  Profit Factor: {metrics['profit_factor']:4.2f} | Retorno Neto: {metrics['net_return_pct']:+6.2f}% | MaxDD: {metrics['max_drawdown_pct']:4.1f}% | Exp: {metrics['expectancy_r']:+.2f}R")

    # Métrica Portfolio Global
    portfolio_metrics = compute_detailed_metrics(all_trades)
    print("\n" + "=" * 85)
    print("RESULTADO GLOBAL DEL PORTFOLIO (TODOS LOS MERCADOS INTEGRADOS)")
    print(f"  Total Operaciones:    {portfolio_metrics['trades']}")
    print(f"  Tasa Acierto TP1:     {portfolio_metrics['win_rate_tp1']:.1f}% (Cierre con ganancias de +1.0%)")
    print(f"  Tasa Acierto TP2:     {portfolio_metrics['win_rate_full']:.1f}% (Cierre completo en 1:3.5)")
    print(f"  Tasa Salvada en BE:   {portfolio_metrics['be_rate']:.1f}% (Protegidas a $0.00 con Spread)")
    print(f"  Profit Factor:        {portfolio_metrics['profit_factor']:.2f}")
    print(f"  Retorno Neto Total:   {portfolio_metrics['net_return_pct']:+.2f}%")
    print(f"  Drawdown Máximo:      {portfolio_metrics['max_drawdown_pct']:.2f}%")
    print(f"  Sharpe Ratio:         {portfolio_metrics['sharpe_ratio']:.2f}")
    print(f"  Expectativa por Trade:{portfolio_metrics['expectancy_r']:+.2f}R")
    print("=" * 85)
    
    # Exportar datos para el Modelo de IA (Meta-Labeling)
    df_export = pd.DataFrame(all_trades)
    if not df_export.empty:
        df_export['total_pnl_r'] = (df_export['leg1_pnl_r'] * 0.5) + (df_export['leg2_pnl_r'] * 0.5)
        df_export['meta_label_won'] = (df_export['total_pnl_r'] > 0).astype(int)
        
        # Guardar CSV de trades
        csv_file = out_dir / "replay_2y_enhanced_smc_trades.csv"
        df_export.to_csv(csv_file, index=False)
        print(f"\n[EXPORT] Trades guardados para auditoría: {csv_file}")
        
        # Guardar dataset para reentrenamiento de IA
        ai_training_samples = []
        for idx, row in df_export.iterrows():
            features = {
                "trade_score": float(row["trade_score"]),
                "confirmation_percentage": float(row["trade_score"]) / 100.0,
                "adx": float(row["adx"]),
                "atr_ratio": float(row["atr_ratio"]),
                "spread_to_sl_ratio": float(row["spread_to_sl_ratio"]),
                "is_forex": 1.0 if row["category"] == "forex" else 0.0,
                "is_gold": 1.0 if row["category"] == "gold" else 0.0,
                "is_volatility": 1.0 if row["category"] == "volatility" else 0.0,
                "is_step": 1.0 if row["category"] == "step" else 0.0,
                "is_jump": 1.0 if row["category"] == "jump" else 0.0,
                "is_boom": 1.0 if row["category"] == "boom" else 0.0,
                "is_crash": 1.0 if row["category"] == "crash" else 0.0,
                "direction_buy": 1.0 if row["direction"] == "BUY" else 0.0,
                "planned_rr": 2.0
            }
            sample = {
                "symbol": row["symbol"],
                "category": row["category"],
                "entry_time": str(row["entry_time"]),
                "features": features,
                "target_won": int(row["meta_label_won"]),
                "realized_r": float(row["total_pnl_r"])
            }
            ai_training_samples.append(sample)
            
        json_file = out_dir / "ai_meta_training_dataset_ready.json"
        with open(json_file, "w", encoding="utf-8") as f:
            json.dump({
                "schema": "meta-features-v5-enhanced",
                "generated_at": datetime.now(timezone.utc).isoformat(),
                "total_samples": len(ai_training_samples),
                "portfolio_metrics": portfolio_metrics,
                "by_asset": {k: {"category": v["category"], "metrics": v["metrics"]} for k, v in results_by_asset.items()},
                "samples": ai_training_samples
            }, f, indent=2)
        print(f"[EXPORT] Dataset de IA guardado listo para reentrenar: {json_file}")

if __name__ == "__main__":
    main()
