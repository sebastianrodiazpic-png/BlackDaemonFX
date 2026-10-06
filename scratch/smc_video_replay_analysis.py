"""
Simulador y Replay Histórico de 2 Años:
Estrategia SMC del Vídeo 'Trading Simple' (H1 Context -> M5 Trigger)
Filtros: Killzones (London/NY), High-Impact News, Spread Guard & Rollover.
Riesgo: 1.0% total por oportunidad (2 entradas de 0.5%), Objetivo 1:2 R:R.
"""

import os
import glob
import math
import numpy as np
import pandas as pd
from datetime import datetime, timezone, timedelta
from zoneinfo import ZoneInfo
from pathlib import Path

NY_TZ = ZoneInfo("America/New_York")
UTC = timezone.utc

# Costes de spread típicos por instrumento
SPREADS = {
    "EURUSD": 0.00012,     # 1.2 pips
    "GBPUSD": 0.00018,     # 1.8 pips
    "USDJPY": 0.015,       # 1.5 pips
    "USDCHF": 0.00015,     # 1.5 pips
    "XAUUSD": 0.59,        # $0.59
    "XAGUSD": 0.055,       # $0.055
    "US_Tech_100": 1.20,   # 1.2 pts
    "US_SP_500": 0.40,     # 0.40 pts
    "Wall_Street_30": 2.20,# 2.2 pts
    "BTCUSD": 20.0,        # $20
    "US_Oil": 0.16         # $0.16
}

PIP_SIZES = {
    "EURUSD": 0.0001,
    "GBPUSD": 0.0001,
    "USDCHF": 0.0001,
    "USDJPY": 0.01,
    "XAUUSD": 0.1,
    "XAGUSD": 0.01,
    "US_Tech_100": 1.0,
    "US_SP_500": 0.1,
    "Wall_Street_30": 1.0,
    "BTCUSD": 1.0,
    "US_Oil": 0.01
}

def is_in_killzone(dt_ny):
    """
    Killzones basadas en hora Nueva York:
    - London Killzone: 02:00 a 05:00 NY
    - New York Killzone: 07:00 a 11:00 NY
    """
    hour = dt_ny.hour
    minute = dt_ny.minute
    t_min = hour * 60 + minute
    
    london_kz = (2 * 60 <= t_min < 5 * 60)
    ny_kz = (7 * 60 <= t_min < 11 * 60)
    return london_kz, ny_kz

def is_market_close_or_rollover(dt_ny):
    """
    Ventana de cierre / rollover:
    - Rollover diario: 16:45 a 17:30 NY (Spread se multiplica)
    - Fin de semana: Viernes a partir de las 16:00 NY hasta Domingo 17:00 NY
    """
    weekday = dt_ny.weekday() # 0=Mon, 4=Fri, 5=Sat, 6=Sun
    hour = dt_ny.hour
    minute = dt_ny.minute
    t_min = hour * 60 + minute
    
    # Fin de semana
    if weekday == 4 and t_min >= 16 * 60:
        return True, "WEEKEND_CLOSE"
    if weekday == 5:
        return True, "WEEKEND_CLOSE"
    if weekday == 6 and t_min < 17 * 60:
        return True, "WEEKEND_CLOSE"
        
    # Rollover diario
    if 16 * 60 + 45 <= t_min < 17 * 60 + 30:
        return True, "DAILY_ROLLOVER"
        
    return False, "OPEN"

def is_high_impact_news_window(dt_ny):
    """
    Ventanas de noticias de alto impacto recurrentes (US Macro):
    - 08:30 NY (NFP, CPI, PPI, Retail Sales, GDP, Jobless Claims) +/- 30 min (08:00 - 09:00)
    - 10:00 NY (ISM Manufacturing / Services, Mich Consumer) +/- 20 min (09:45 - 10:20)
    - 14:00 NY (FOMC Rate Decision / Powell Conference, Miércoles) +/- 45 min (13:30 - 14:45)
    """
    hour = dt_ny.hour
    minute = dt_ny.minute
    t_min = hour * 60 + minute
    weekday = dt_ny.weekday()
    
    # 08:30 ventana
    if 8 * 60 <= t_min <= 9 * 60:
        return True, "NEWS_0830_MACRO"
        
    # 10:00 ventana
    if 9 * 60 + 45 <= t_min <= 10 * 60 + 20:
        return True, "NEWS_1000_ISM"
        
    # 14:00 FOMC (típicamente miércoles)
    if weekday == 2 and (13 * 60 + 30 <= t_min <= 14 * 60 + 45):
        return True, "NEWS_1400_FOMC"
        
    return False, "NO_NEWS"

def detect_h1_fvgs_and_structure(h1_df):
    """
    En H1:
    1. Swing points para estructura (BOS / CHoCH)
    2. Fair Value Gaps (Bullish & Bearish)
    3. Rango de descuento / premium (50% de Fibonacci del swing activo)
    """
    df = h1_df.copy().reset_index(drop=True)
    n = len(df)
    
    # Detectar FVG en H1
    bullish_fvgs = [] # (index_formed, top, bottom, mitigated)
    bearish_fvgs = []
    
    # Usamos lookback para swings simples de 3 velas (High[i] > High[i-1] and High[i] > High[i+1])
    highs = df['high'].values
    lows = df['low'].values
    closes = df['close'].values
    times = df['time'].values
    
    for i in range(2, n):
        # Bullish FVG: Low de vela i > High de vela i-2
        if lows[i] > highs[i-2]:
            fvg_top = lows[i]
            fvg_bottom = highs[i-2]
            fvg_size = fvg_top - fvg_bottom
            if fvg_size > 0:
                bullish_fvgs.append({
                    "bar_idx": i,
                    "time": times[i],
                    "top": fvg_top,
                    "bottom": fvg_bottom,
                    "mitigated": False,
                    "mitigated_idx": None
                })
                
        # Bearish FVG: High de vela i < Low de vela i-2
        if highs[i] < lows[i-2]:
            fvg_top = lows[i-2]
            fvg_bottom = highs[i]
            fvg_size = fvg_top - fvg_bottom
            if fvg_size > 0:
                bearish_fvgs.append({
                    "bar_idx": i,
                    "time": times[i],
                    "top": fvg_top,
                    "bottom": fvg_bottom,
                    "mitigated": False,
                    "mitigated_idx": None
                })
                
    return df, bullish_fvgs, bearish_fvgs

def run_smc_replay(symbol, m5_df, h1_df, config):
    """
    Simula la estrategia completa con control de velas paso a paso.
    """
    spread = SPREADS.get(symbol, 0.5)
    pip_size = PIP_SIZES.get(symbol, 0.0001)
    
    m5_df = m5_df.copy().sort_values('time').reset_index(drop=True)
    h1_df = h1_df.copy().sort_values('time').reset_index(drop=True)
    
    m5_df['time'] = pd.to_datetime(m5_df['time'], utc=True)
    h1_df['time'] = pd.to_datetime(h1_df['time'], utc=True)
    
    m5_times = m5_df['time'].values
    h1_times = h1_df['time'].values
    
    h1_df, h1_bull_fvgs, h1_bear_fvgs = detect_h1_fvgs_and_structure(h1_df)
    
    trades = []
    active_trades = []
    
    # Pre-calcular swings locales en M5 (lookback 5 velas)
    m5_highs = m5_df['high'].values
    m5_lows = m5_df['low'].values
    m5_closes = m5_df['close'].values
    m5_opens = m5_df['open'].values
    
    # Estado de seguimiento
    # Buscamos: Precio dentro de FVG H1 activo -> Liquidity Sweep en M5 -> CHoCH en M5 -> Entrada dual (1:2 R:R)
    
    # Cooldown para no saturar de entradas el mismo movimiento
    last_entry_time = None
    min_entry_interval = timedelta(hours=2)
    
    for i in range(20, len(m5_df)):
        cur_t_dt = pd.Timestamp(m5_times[i]).to_pydatetime()
        cur_t_ny = cur_t_dt.astimezone(NY_TZ)
        
        # 1. Gestionar trades activos primero
        cur_high = m5_highs[i]
        cur_low = m5_lows[i]
        cur_close = m5_closes[i]
        
        # Revisar cierre de trades abiertos
        remaining_active = []
        for tr in active_trades:
            # Comprobar Rollover / Weekend close forzoso si la política lo exige
            is_close, close_reason = is_market_close_or_rollover(cur_t_ny)
            
            # Verificar SL / TP con spread
            direction = tr['direction']
            sl = tr['sl']
            tp1 = tr['tp1']
            tp2 = tr['tp2']
            
            # Para BUY: el stop toca en Bid (cur_low), TP en Bid (cur_high)
            # Para SELL: el stop toca en Ask (cur_high + spread), TP en Ask (cur_low + spread)
            closed_leg1 = tr['leg1_closed']
            closed_leg2 = tr['leg2_closed']
            
            if direction == 'BUY':
                # Check Stop Loss
                if cur_low <= sl:
                    if not closed_leg1:
                        tr['leg1_pnl_r'] = -1.0 # Perdió 0.5%
                        tr['leg1_exit_time'] = cur_t_dt
                        tr['leg1_exit_price'] = sl
                        tr['leg1_closed'] = True
                    if not closed_leg2:
                        # Si leg 2 estaba en break-even
                        if tr['leg2_be_active']:
                            tr['leg2_pnl_r'] = 0.0
                            tr['leg2_exit_price'] = tr['entry_price'] + spread
                        else:
                            tr['leg2_pnl_r'] = -1.0
                        tr['leg2_exit_time'] = cur_t_dt
                        tr['leg2_closed'] = True
                    trades.append(tr)
                    continue
                    
                # Check TP1 (1:2)
                if not closed_leg1 and cur_high >= tp1:
                    tr['leg1_pnl_r'] = 2.0 # Ganó 1:2 (+1.0% de cuenta, arriesgando 0.5%)
                    tr['leg1_exit_time'] = cur_t_dt
                    tr['leg1_exit_price'] = tp1
                    tr['leg1_closed'] = True
                    # Al tocar TP1, mover Leg 2 a Break-Even!
                    tr['sl'] = tr['entry_price'] + spread
                    tr['leg2_be_active'] = True
                    
                # Check TP2 (1:2 en este test base)
                if not closed_leg2 and cur_high >= tp2:
                    tr['leg2_pnl_r'] = 2.0
                    tr['leg2_exit_time'] = cur_t_dt
                    tr['leg2_exit_price'] = tp2
                    tr['leg2_closed'] = True
                    
            elif direction == 'SELL':
                ask_high = cur_high + spread
                ask_low = cur_low + spread
                
                # Check Stop Loss
                if ask_high >= sl:
                    if not closed_leg1:
                        tr['leg1_pnl_r'] = -1.0
                        tr['leg1_exit_time'] = cur_t_dt
                        tr['leg1_exit_price'] = sl
                        tr['leg1_closed'] = True
                    if not closed_leg2:
                        if tr['leg2_be_active']:
                            tr['leg2_pnl_r'] = 0.0
                            tr['leg2_exit_price'] = tr['entry_price']
                        else:
                            tr['leg2_pnl_r'] = -1.0
                        tr['leg2_exit_time'] = cur_t_dt
                        tr['leg2_closed'] = True
                    trades.append(tr)
                    continue
                    
                # Check TP1
                if not closed_leg1 and ask_low <= tp1:
                    tr['leg1_pnl_r'] = 2.0
                    tr['leg1_exit_time'] = cur_t_dt
                    tr['leg1_exit_price'] = tp1
                    tr['leg1_closed'] = True
                    tr['sl'] = tr['entry_price'] - spread
                    tr['leg2_be_active'] = True
                    
                # Check TP2
                if not closed_leg2 and ask_low <= tp2:
                    tr['leg2_pnl_r'] = 2.0
                    tr['leg2_exit_time'] = cur_t_dt
                    tr['leg2_exit_price'] = tp2
                    tr['leg2_closed'] = True
                    
            # Si ambas piernas cerradas
            if tr['leg1_closed'] and tr['leg2_closed']:
                trades.append(tr)
            else:
                # Si llega el cierre de viernes, cerrar forzosamente a mercado
                if config.get("force_weekend_close", True) and is_close and close_reason == "WEEKEND_CLOSE":
                    exit_p = cur_close if direction == 'BUY' else (cur_close + spread)
                    risk_dist = abs(tr['entry_price'] - tr['orig_sl'])
                    pnl_r = ((exit_p - tr['entry_price']) / risk_dist) if direction == 'BUY' else ((tr['entry_price'] - exit_p) / risk_dist)
                    if not tr['leg1_closed']:
                        tr['leg1_pnl_r'] = pnl_r
                        tr['leg1_exit_time'] = cur_t_dt
                        tr['leg1_exit_price'] = exit_p
                        tr['leg1_closed'] = True
                    if not tr['leg2_closed']:
                        tr['leg2_pnl_r'] = pnl_r
                        tr['leg2_exit_time'] = cur_t_dt
                        tr['leg2_exit_price'] = exit_p
                        tr['leg2_closed'] = True
                    tr['exit_reason'] = "WEEKEND_FORCED_CLOSE"
                    trades.append(tr)
                else:
                    remaining_active.append(tr)
                    
        active_trades = remaining_active
        
        # Max operaciones simultáneas
        if len(active_trades) >= config.get("max_active_trades", 1):
            continue
            
        # Cooldown
        if last_entry_time and (cur_t_dt - last_entry_time) < min_entry_interval:
            continue
            
        # 2. FILTROS DE ENTORNO:
        # A) Rollover / Cierre de mercado
        is_close, close_reason = is_market_close_or_rollover(cur_t_ny)
        if config.get("filter_rollover", True) and is_close:
            continue
            
        # B) Killzone filter
        is_london, is_ny = is_in_killzone(cur_t_ny)
        in_kz = is_london or is_ny
        if config.get("filter_killzone", True) and not in_kz:
            continue
            
        # C) Noticias de alto impacto
        has_news, news_reason = is_high_impact_news_window(cur_t_ny)
        if config.get("filter_news", True) and has_news:
            continue
            
        # 3. DETECCIÓN DE CONTEXTO H1 (Sin Lookahead Bias):
        # Tomar velas H1 cerradas estrictamente antes de cur_t_dt
        t_val = m5_times[i]
        h1_idx = np.searchsorted(h1_times, t_val, side='left')
        if h1_idx < 10:
            continue
            
        recent_h1_close = h1_df['close'].iloc[h1_idx - 1]
        
        # Buscar FVGs de H1 recientes (últimas 24 velas de H1)
        valid_bull_fvgs = [
            fvg for fvg in h1_bull_fvgs 
            if (h1_idx - 24 <= fvg['bar_idx'] < h1_idx)
        ]
        valid_bear_fvgs = [
            fvg for fvg in h1_bear_fvgs 
            if (h1_idx - 24 <= fvg['bar_idx'] < h1_idx)
        ]
        
        # Evaluar BUY: ¿Precio actual M5 dentro de un Bullish FVG de H1?
        inside_bull_fvg = any(fvg['bottom'] <= cur_low <= fvg['top'] or fvg['bottom'] <= cur_close <= fvg['top'] for fvg in valid_bull_fvgs)
        
        # Evaluar SELL: ¿Precio actual M5 dentro de un Bearish FVG de H1?
        inside_bear_fvg = any(fvg['bottom'] <= cur_high <= fvg['top'] or fvg['bottom'] <= cur_close <= fvg['top'] for fvg in valid_bear_fvgs)
        
        if not (inside_bull_fvg or inside_bear_fvg):
            continue
            
        # 4. GATILLO M5:
        # Barrida de liquidez + CHoCH en M5
        # Lookback local de pivotes M5
        sub_highs = m5_highs[i-15 : i]
        sub_lows = m5_lows[i-15 : i]
        sub_closes = m5_closes[i-15 : i]
        
        local_swing_low = np.min(sub_lows[:-2])
        local_swing_high = np.max(sub_highs[:-2])
        
        # A) Setup BUY:
        if inside_bull_fvg:
            # Barrida: alguna de las últimas 3 velas perforó el mínimo local con mecha pero cerró arriba o rebotó
            swept = any(m5_lows[i-k] < local_swing_low and m5_closes[i-k] > local_swing_low for k in range(1, 4))
            # CHoCH: vela actual o previa rompe el máximo local intermedio con cuerpo
            choch_level = np.max(sub_highs[-5:-1])
            choch = cur_close > choch_level and m5_closes[i-1] <= choch_level
            
            if swept and choch:
                sweep_low = min(m5_lows[i-k] for k in range(1, 5))
                sl_price = sweep_low - (spread * 1.5)
                entry_price = cur_close + spread # Compramos al Ask
                sl_distance = entry_price - sl_price
                
                # Spread Protection: Spread no debe exceder el 10% del SL
                if sl_distance > 0 and (spread / sl_distance) <= config.get("max_spread_risk_ratio", 0.10):
                    tp_dist = sl_distance * 2.0 # Ratio 1:2
                    tp1 = entry_price + tp_dist
                    tp2 = entry_price + tp_dist # Ambas buscan 1:2
                    
                    trade = {
                        "symbol": symbol,
                        "direction": "BUY",
                        "entry_time": cur_t_dt,
                        "entry_price": entry_price,
                        "sl": sl_price,
                        "orig_sl": sl_price,
                        "tp1": tp1,
                        "tp2": tp2,
                        "sl_dist": sl_distance,
                        "risk_pct": 1.0, # 1% total (0.5% leg1 + 0.5% leg2)
                        "leg1_closed": False,
                        "leg2_closed": False,
                        "leg2_be_active": False,
                        "leg1_pnl_r": 0.0,
                        "leg2_pnl_r": 0.0,
                        "kz": "LONDON" if is_london else ("NY" if is_ny else "OTHER"),
                        "exit_reason": "TP_OR_SL"
                    }
                    active_trades.append(trade)
                    last_entry_time = cur_t_dt
                    continue
                    
        # B) Setup SELL:
        if inside_bear_fvg:
            swept = any(m5_highs[i-k] > local_swing_high and m5_closes[i-k] < local_swing_high for k in range(1, 4))
            choch_level = np.min(sub_lows[-5:-1])
            choch = cur_close < choch_level and m5_closes[i-1] >= choch_level
            
            if swept and choch:
                sweep_high = max(m5_highs[i-k] for k in range(1, 5))
                sl_price = sweep_high + (spread * 2.5) # SL sobre mecha + spread buffer
                entry_price = cur_close # Vendemos al Bid
                sl_distance = sl_price - entry_price
                
                if sl_distance > 0 and (spread / sl_distance) <= config.get("max_spread_risk_ratio", 0.10):
                    tp_dist = sl_distance * 2.0 # Ratio 1:2
                    tp1 = entry_price - tp_dist
                    tp2 = entry_price - tp_dist
                    
                    trade = {
                        "symbol": symbol,
                        "direction": "SELL",
                        "entry_time": cur_t_dt,
                        "entry_price": entry_price,
                        "sl": sl_price,
                        "orig_sl": sl_price,
                        "tp1": tp1,
                        "tp2": tp2,
                        "sl_dist": sl_distance,
                        "risk_pct": 1.0,
                        "leg1_closed": False,
                        "leg2_closed": False,
                        "leg2_be_active": False,
                        "leg1_pnl_r": 0.0,
                        "leg2_pnl_r": 0.0,
                        "kz": "LONDON" if is_london else ("NY" if is_ny else "OTHER"),
                        "exit_reason": "TP_OR_SL"
                    }
                    active_trades.append(trade)
                    last_entry_time = cur_t_dt
                    continue
                    
    return trades

def calculate_metrics(trades_list, initial_capital=10000.0):
    if not trades_list:
        return {
            "total_trades": 0, "win_rate": 0, "profit_factor": 0,
            "net_profit": 0, "net_return_pct": 0, "max_drawdown_pct": 0,
            "sharpe_ratio": 0, "expectancy_r": 0
        }
        
    df = pd.DataFrame(trades_list)
    # Cada trade arriesga 1% total: 0.5% en pierna 1 y 0.5% en pierna 2
    # El PnL total en R respecto al 1% de la cuenta:
    # leg1_pnl_r * 0.5 + leg2_pnl_r * 0.5
    df['total_pnl_r'] = (df['leg1_pnl_r'] * 0.5) + (df['leg2_pnl_r'] * 0.5)
    
    total_trades = len(df)
    winning_trades = df[df['total_pnl_r'] > 0]
    losing_trades = df[df['total_pnl_r'] < 0]
    breakeven_trades = df[df['total_pnl_r'] == 0]
    
    win_rate = (len(winning_trades) / total_trades) * 100 if total_trades > 0 else 0
    
    gross_win_r = winning_trades['total_pnl_r'].sum()
    gross_loss_r = abs(losing_trades['total_pnl_r'].sum())
    
    profit_factor = (gross_win_r / gross_loss_r) if gross_loss_r > 0 else (999.0 if gross_win_r > 0 else 0)
    
    # Curva de equidad
    balance = initial_capital
    balances = [balance]
    peak = balance
    drawdowns = [0.0]
    
    for r in df['total_pnl_r']:
        dollar_pnl = balance * (r * 0.01) # 1 R = 1%
        balance += dollar_pnl
        balances.append(balance)
        if balance > peak:
            peak = balance
        dd = (peak - balance) / peak * 100
        drawdowns.append(dd)
        
    net_profit = balance - initial_capital
    net_return_pct = (net_profit / initial_capital) * 100
    max_dd = max(drawdowns) if drawdowns else 0
    
    expectancy_r = df['total_pnl_r'].mean()
    sharpe = (df['total_pnl_r'].mean() / df['total_pnl_r'].std() * math.sqrt(252)) if df['total_pnl_r'].std() > 0 else 0
    
    return {
        "total_trades": total_trades,
        "win_rate": win_rate,
        "profit_factor": profit_factor,
        "net_profit": net_profit,
        "net_return_pct": net_return_pct,
        "max_drawdown_pct": max_dd,
        "sharpe_ratio": sharpe,
        "expectancy_r": expectancy_r,
        "gross_win_r": gross_win_r,
        "gross_loss_r": gross_loss_r
    }

def main():
    print("=" * 80)
    print("INICIANDO REPLAY HISTÓRICO SMC 2 AÑOS (H1 FVG -> M5 SWEEP & CHOCH)")
    print("Objetivo: 1:2 R:R | Riesgo: 1.0% (2 piernas de 0.5%)")
    print("Filtros: Killzones (London/NY), High-Impact News, Spread Guard & Rollover")
    print("=" * 80)
    
    # Instrumentos a procesar
    instruments = [
        # Forex
        ("EURUSD", "data/forex_historical/EURUSD_M5.csv", "data/forex_historical/EURUSD_H1.csv"),
        ("GBPUSD", "data/forex_historical/GBPUSD_M5.csv", "data/forex_historical/GBPUSD_H1.csv"),
        ("USDJPY", "data/forex_historical/USDJPY_M5.csv", "data/forex_historical/USDJPY_H1.csv"),
        ("USDCHF", "data/forex_historical/USDCHF_M5.csv", "data/forex_historical/USDCHF_H1.csv"),
        # Metales y Commodities
        ("XAUUSD", "data/historical/XAUUSD_M5.csv", "data/historical/XAUUSD_H1.csv"),
        ("XAGUSD", "data/historical/XAGUSD_M5.csv", "data/historical/XAGUSD_H1.csv"),
        ("US_Oil", "data/historical/US_Oil_M5.csv", "data/historical/US_Oil_H1.csv"),
        # Índices
        ("US_Tech_100", "data/historical/US_Tech_100_M5.csv", "data/historical/US_Tech_100_H1.csv"),
        ("US_SP_500", "data/historical/US_SP_500_M5.csv", "data/historical/US_SP_500_H1.csv"),
        ("Wall_Street_30", "data/historical/Wall_Street_30_M5.csv", "data/historical/Wall_Street_30_H1.csv"),
        # Cripto
        ("BTCUSD", "data/historical/BTCUSD_M5.csv", "data/historical/BTCUSD_H1.csv"),
    ]
    
    # 2 Variantes de prueba para comparar el impacto real de los filtros:
    # 1. Estrategia Completa con Filtros (Killzones + News Filter + Rollover/Spread Guard)
    # 2. Estrategia 'Raw' sin filtros (operando 24/7 sin importar rollover ni noticias)
    
    configs = {
        "SMC_CON_FILTROS_TOTALES": {
            "filter_killzone": True,
            "filter_news": True,
            "filter_rollover": True,
            "force_weekend_close": True,
            "max_spread_risk_ratio": 0.10,
            "max_active_trades": 1
        },
        "SMC_CRUDA_SIN_FILTROS": {
            "filter_killzone": False,
            "filter_news": False,
            "filter_rollover": False,
            "force_weekend_close": False,
            "max_spread_risk_ratio": 0.30,
            "max_active_trades": 1
        }
    }
    
    all_results = {}
    
    for cfg_name, cfg in configs.items():
        print(f"\n>>> EJECUTANDO ESCENARIO: {cfg_name} <<<")
        results_by_sym = {}
        combined_trades = []
        
        for sym, m5_p, h1_p in instruments:
            if not os.path.exists(m5_p) or not os.path.exists(h1_p):
                print(f"  [OMITIDO] {sym}: Faltan archivos de datos.")
                continue
                
            m5_df = pd.read_csv(m5_p)
            h1_df = pd.read_csv(h1_p)
            
            trades = run_smc_replay(sym, m5_df, h1_df, cfg)
            combined_trades.extend(trades)
            metrics = calculate_metrics(trades)
            results_by_sym[sym] = (metrics, len(trades))
            
            print(f"  {sym:14} | Trades: {metrics['total_trades']:4} | WinRate: {metrics['win_rate']:5.1f}% | PF: {metrics['profit_factor']:4.2f} | Net: {metrics['net_return_pct']:+6.1f}% | MaxDD: {metrics['max_drawdown_pct']:4.1f}%")
            
        combined_metrics = calculate_metrics(combined_trades)
        all_results[cfg_name] = {
            "by_symbol": results_by_sym,
            "portfolio": combined_metrics,
            "trades": combined_trades
        }
        print(f"--- TOTAL PORTFOLIO ({cfg_name}) ---")
        print(f"  Trades: {combined_metrics['total_trades']} | WinRate: {combined_metrics['win_rate']:.1f}% | Profit Factor: {combined_metrics['profit_factor']:.2f}")
        print(f"  Retorno Neto: {combined_metrics['net_return_pct']:+.2f}% | Max Drawdown: {combined_metrics['max_drawdown_pct']:.2f}% | Sharpe: {combined_metrics['sharpe_ratio']:.2f} | Expectancy: {combined_metrics['expectancy_r']:+.2f}R")

    # Guardar resumen en CSV para inspección
    out_dir = Path("storage/analysis")
    out_dir.mkdir(parents=True, exist_ok=True)
    summary_rows = []
    for cfg_name, data in all_results.items():
        for sym, (m, count) in data["by_symbol"].items():
            summary_rows.append({
                "scenario": cfg_name,
                "symbol": sym,
                "trades": m["total_trades"],
                "win_rate": round(m["win_rate"], 2),
                "profit_factor": round(m["profit_factor"], 2),
                "net_return_pct": round(m["net_return_pct"], 2),
                "max_drawdown_pct": round(m["max_drawdown_pct"], 2),
                "expectancy_r": round(m["expectancy_r"], 2)
            })
    pd.DataFrame(summary_rows).to_csv(out_dir / "smc_replay_2years_summary.csv", index=False)
    print("\n[ÉXITO] Resultados guardados en storage/analysis/smc_replay_2years_summary.csv")

if __name__ == "__main__":
    main()
