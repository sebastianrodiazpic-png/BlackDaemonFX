"""
Test de Optimización SMC Cuantitativo:
1. Filtro Premium / Discount en H1 (Fibonacci 50%).
2. Exigencia de Desplazamiento en la vela de CHoCH M5 (body / range >= 0.55).
3. Comparar R:R 1:2 fijo vs Gestión Asimétrica (Leg 1 TP a 1:1.5 asegurando + Leg 2 TP a 1:3.0).
"""

import os
import math
import numpy as np
import pandas as pd
from datetime import datetime, timezone, timedelta
from zoneinfo import ZoneInfo
from pathlib import Path

NY_TZ = ZoneInfo("America/New_York")

SPREADS = {
    "EURUSD": 0.00012,
    "GBPUSD": 0.00018,
    "USDJPY": 0.015,
    "USDCHF": 0.00015,
    "XAUUSD": 0.59,
    "XAGUSD": 0.055,
    "US_Tech_100": 1.20,
    "US_SP_500": 0.40,
    "Wall_Street_30": 2.20,
    "BTCUSD": 20.0,
    "US_Oil": 0.16
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
    if (weekday == 4 and t_min >= 16 * 60) or weekday == 5 or (weekday == 6 and t_min < 17 * 60):
        return True, "WEEKEND_CLOSE"
    if 16 * 60 + 45 <= t_min < 17 * 60 + 30:
        return True, "DAILY_ROLLOVER"
    return False, "OPEN"

def is_high_impact_news_window(dt_ny):
    hour = dt_ny.hour
    minute = dt_ny.minute
    t_min = hour * 60 + minute
    weekday = dt_ny.weekday()
    if 8 * 60 <= t_min <= 9 * 60:
        return True, "NEWS_0830_MACRO"
    if 9 * 60 + 45 <= t_min <= 10 * 60 + 20:
        return True, "NEWS_1000_ISM"
    if weekday == 2 and (13 * 60 + 30 <= t_min <= 14 * 60 + 45):
        return True, "NEWS_1400_FOMC"
    return False, "NO_NEWS"

def run_optimized_test(tp1_r=1.5, tp2_r=3.0, require_premium_discount=True, require_displacement=True):
    instruments = [
        ("EURUSD", "data/forex_historical/EURUSD_M5.csv", "data/forex_historical/EURUSD_H1.csv"),
        ("GBPUSD", "data/forex_historical/GBPUSD_M5.csv", "data/forex_historical/GBPUSD_H1.csv"),
        ("USDJPY", "data/forex_historical/USDJPY_M5.csv", "data/forex_historical/USDJPY_H1.csv"),
        ("USDCHF", "data/forex_historical/USDCHF_M5.csv", "data/forex_historical/USDCHF_H1.csv"),
        ("XAUUSD", "data/historical/XAUUSD_M5.csv", "data/historical/XAUUSD_H1.csv"),
        ("XAGUSD", "data/historical/XAGUSD_M5.csv", "data/historical/XAGUSD_H1.csv"),
        ("US_Tech_100", "data/historical/US_Tech_100_M5.csv", "data/historical/US_Tech_100_H1.csv"),
        ("US_SP_500", "data/historical/US_SP_500_M5.csv", "data/historical/US_SP_500_H1.csv"),
        ("Wall_Street_30", "data/historical/Wall_Street_30_M5.csv", "data/historical/Wall_Street_30_H1.csv"),
        ("BTCUSD", "data/historical/BTCUSD_M5.csv", "data/historical/BTCUSD_H1.csv"),
    ]
    
    all_trades = []
    
    for sym, m5_p, h1_p in instruments:
        if not os.path.exists(m5_p) or not os.path.exists(h1_p):
            continue
        spread = SPREADS.get(sym, 0.5)
        m5_df = pd.read_csv(m5_p).sort_values('time').reset_index(drop=True)
        h1_df = pd.read_csv(h1_p).sort_values('time').reset_index(drop=True)
        
        m5_df['time'] = pd.to_datetime(m5_df['time'], utc=True)
        h1_df['time'] = pd.to_datetime(h1_df['time'], utc=True)
        
        m5_times = m5_df['time'].values
        h1_times = h1_df['time'].values
        
        m5_highs = m5_df['high'].values
        m5_lows = m5_df['low'].values
        m5_closes = m5_df['close'].values
        m5_opens = m5_df['open'].values
        
        h1_highs = h1_df['high'].values
        h1_lows = h1_df['low'].values
        
        # Detectar FVGs H1
        bull_fvgs = []
        bear_fvgs = []
        for j in range(2, len(h1_df)):
            if h1_lows[j] > h1_highs[j-2]:
                bull_fvgs.append((j, h1_highs[j-2], h1_lows[j])) # bottom, top
            if h1_highs[j] < h1_lows[j-2]:
                bear_fvgs.append((j, h1_highs[j], h1_lows[j-2]))
                
        active_trades = []
        sym_trades = []
        last_entry = None
        
        for i in range(20, len(m5_df)):
            cur_t = pd.Timestamp(m5_times[i]).to_pydatetime()
            cur_t_ny = cur_t.astimezone(NY_TZ)
            
            cur_h = m5_highs[i]
            cur_l = m5_lows[i]
            cur_c = m5_closes[i]
            cur_o = m5_opens[i]
            
            # Gestionar activos
            rem = []
            for tr in active_trades:
                direction = tr['direction']
                sl = tr['sl']
                tp1 = tr['tp1']
                tp2 = tr['tp2']
                
                if direction == 'BUY':
                    if cur_l <= sl:
                        if not tr['leg1_closed']:
                            tr['leg1_pnl_r'] = -1.0
                            tr['leg1_closed'] = True
                        if not tr['leg2_closed']:
                            tr['leg2_pnl_r'] = 0.0 if tr['leg2_be'] else -1.0
                            tr['leg2_closed'] = True
                        sym_trades.append(tr)
                        continue
                    if not tr['leg1_closed'] and cur_h >= tp1:
                        tr['leg1_pnl_r'] = tp1_r
                        tr['leg1_closed'] = True
                        tr['sl'] = tr['entry_p'] + spread
                        tr['leg2_be'] = True
                    if not tr['leg2_closed'] and cur_h >= tp2:
                        tr['leg2_pnl_r'] = tp2_r
                        tr['leg2_closed'] = True
                else: # SELL
                    ask_h = cur_h + spread
                    ask_l = cur_l + spread
                    if ask_h >= sl:
                        if not tr['leg1_closed']:
                            tr['leg1_pnl_r'] = -1.0
                            tr['leg1_closed'] = True
                        if not tr['leg2_closed']:
                            tr['leg2_pnl_r'] = 0.0 if tr['leg2_be'] else -1.0
                            tr['leg2_closed'] = True
                        sym_trades.append(tr)
                        continue
                    if not tr['leg1_closed'] and ask_l <= tp1:
                        tr['leg1_pnl_r'] = tp1_r
                        tr['leg1_closed'] = True
                        tr['sl'] = tr['entry_p'] - spread
                        tr['leg2_be'] = True
                    if not tr['leg2_closed'] and ask_l <= tp2:
                        tr['leg2_pnl_r'] = tp2_r
                        tr['leg2_closed'] = True
                        
                if tr['leg1_closed'] and tr['leg2_closed']:
                    sym_trades.append(tr)
                else:
                    is_close, rson = is_market_close_or_rollover(cur_t_ny)
                    if is_close and rson == "WEEKEND_CLOSE":
                        # Forzar cierre
                        exit_p = cur_c if direction == 'BUY' else (cur_c + spread)
                        risk_d = abs(tr['entry_p'] - tr['orig_sl'])
                        pnl_r = ((exit_p - tr['entry_p'])/risk_d) if direction == 'BUY' else ((tr['entry_p'] - exit_p)/risk_d)
                        if not tr['leg1_closed']: tr['leg1_pnl_r'] = pnl_r; tr['leg1_closed'] = True
                        if not tr['leg2_closed']: tr['leg2_pnl_r'] = pnl_r; tr['leg2_closed'] = True
                        sym_trades.append(tr)
                    else:
                        rem.append(tr)
            active_trades = rem
            
            if len(active_trades) >= 1:
                continue
            if last_entry and (cur_t - last_entry) < timedelta(hours=2):
                continue
                
            # Filtros sesión & news & rollover
            is_close, _ = is_market_close_or_rollover(cur_t_ny)
            if is_close: continue
            lz, nyz = is_in_killzone(cur_t_ny)
            if not (lz or nyz): continue
            news, _ = is_high_impact_news_window(cur_t_ny)
            if news: continue
            
            # H1 Context
            h1_idx = np.searchsorted(h1_times, m5_times[i], side='left')
            if h1_idx < 25: continue
            
            # Rango H1 de las ultimas 24 horas (para Discount / Premium)
            h1_swing_high = np.max(h1_highs[h1_idx-24:h1_idx])
            h1_swing_low = np.min(h1_lows[h1_idx-24:h1_idx])
            h1_midpoint = (h1_swing_high + h1_swing_low) / 2.0
            
            recent_bull_fvgs = [f for f in bull_fvgs if h1_idx-24 <= f[0] < h1_idx]
            recent_bear_fvgs = [f for f in bear_fvgs if h1_idx-24 <= f[0] < h1_idx]
            
            inside_bull = any(f[1] <= cur_l <= f[2] or f[1] <= cur_c <= f[2] for f in recent_bull_fvgs)
            inside_bear = any(f[1] <= cur_h <= f[2] or f[1] <= cur_c <= f[2] for f in recent_bear_fvgs)
            
            if not (inside_bull or inside_bear): continue
            
            # Filtro Descuento / Premium
            if require_premium_discount:
                if inside_bull and cur_c > h1_midpoint: # No comprar en Premium
                    inside_bull = False
                if inside_bear and cur_c < h1_midpoint: # No vender en Descuento
                    inside_bear = False
            if not (inside_bull or inside_bear): continue
            
            sub_h = m5_highs[i-15:i]
            sub_l = m5_lows[i-15:i]
            local_low = np.min(sub_l[:-2])
            local_high = np.max(sub_h[:-2])
            
            # Vela de disparo
            candle_range = cur_h - cur_l
            candle_body = abs(cur_c - cur_o)
            displacement_ok = (candle_body / candle_range >= 0.50) if (candle_range > 0 and require_displacement) else True
            
            if inside_bull:
                swept = any(m5_lows[i-k] < local_low and m5_closes[i-k] > local_low for k in range(1, 4))
                choch_level = np.max(sub_h[-5:-1])
                choch = cur_c > choch_level and m5_closes[i-1] <= choch_level
                
                if swept and choch and displacement_ok:
                    sw_low = min(m5_lows[i-k] for k in range(1, 5))
                    sl = sw_low - (spread * 1.5)
                    ep = cur_c + spread
                    sl_dist = ep - sl
                    if sl_dist > 0 and (spread / sl_dist) <= 0.10:
                        tr = {
                            "symbol": sym, "direction": "BUY", "entry_p": ep,
                            "sl": sl, "orig_sl": sl, "tp1": ep + sl_dist * tp1_r,
                            "tp2": ep + sl_dist * tp2_r, "leg1_closed": False,
                            "leg2_closed": False, "leg2_be": False,
                            "leg1_pnl_r": 0.0, "leg2_pnl_r": 0.0
                        }
                        active_trades.append(tr)
                        last_entry = cur_t
                        continue
                        
            if inside_bear:
                swept = any(m5_highs[i-k] > local_high and m5_closes[i-k] < local_high for k in range(1, 4))
                choch_level = np.min(sub_l[-5:-1])
                choch = cur_c < choch_level and m5_closes[i-1] >= choch_level
                
                if swept and choch and displacement_ok:
                    sw_high = max(m5_highs[i-k] for k in range(1, 5))
                    sl = sw_high + (spread * 2.5)
                    ep = cur_c
                    sl_dist = sl - ep
                    if sl_dist > 0 and (spread / sl_dist) <= 0.10:
                        tr = {
                            "symbol": sym, "direction": "SELL", "entry_p": ep,
                            "sl": sl, "orig_sl": sl, "tp1": ep - sl_dist * tp1_r,
                            "tp2": ep - sl_dist * tp2_r, "leg1_closed": False,
                            "leg2_closed": False, "leg2_be": False,
                            "leg1_pnl_r": 0.0, "leg2_pnl_r": 0.0
                        }
                        active_trades.append(tr)
                        last_entry = cur_t
                        continue
                        
        all_trades.extend(sym_trades)
        
    df = pd.DataFrame(all_trades)
    if len(df) == 0:
        return 0, 0, 0, 0, 0
    df['total_pnl_r'] = (df['leg1_pnl_r'] * 0.5) + (df['leg2_pnl_r'] * 0.5)
    wins = df[df['total_pnl_r'] > 0]
    losses = df[df['total_pnl_r'] < 0]
    wr = len(wins) / len(df) * 100
    gw = wins['total_pnl_r'].sum()
    gl = abs(losses['total_pnl_r'].sum())
    pf = gw / gl if gl > 0 else 999.0
    
    bal = 10000.0
    peak = bal
    dds = []
    for r in df['total_pnl_r']:
        bal += bal * (r * 0.01)
        if bal > peak: peak = bal
        dds.append((peak - bal)/peak * 100)
    ret = (bal - 10000.0)/10000.0 * 100
    mdd = max(dds) if dds else 0
    
    return len(df), wr, pf, ret, mdd

if __name__ == "__main__":
    print("TEST COMPARATIVO DE ASIGNACIÓN DE TARGETS Y FILTROS:")
    for name, (tp1, tp2, pd_filter, disp_filter) in {
        "Base 1:2 R:R (Video puro)": (2.0, 2.0, False, False),
        "Filtro Discount/Premium + Displacement (1:2 R:R)": (2.0, 2.0, True, True),
        "Gestión Dual Asimétrica (TP1 1:1.5 + BE + TP2 1:3.0)": (1.5, 3.0, True, True),
        "Gestión Dual Asimétrica (TP1 1:2.0 + BE + TP2 1:4.0)": (2.0, 4.0, True, True)
    }.items():
        n, wr, pf, ret, mdd = run_optimized_test(tp1, tp2, pd_filter, disp_filter)
        print(f"{name:55} | Trades: {n:3} | WR: {wr:4.1f}% | PF: {pf:4.2f} | Ret: {ret:+6.1f}% | MDD: {mdd:4.1f}%")
