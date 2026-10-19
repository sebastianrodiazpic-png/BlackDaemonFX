"""
scratch/evaluate_orb_session_strategies.py
=========================================
Evaluación cuantitativa de Opening Range Breakout (ORB) en instrumentos con sesiones relevantes:
- Forex: EURUSD, GBPUSD, USDJPY, AUDNZD (Sesión de Londres: Rango 07:00-07:30 UTC)
- Metales e Índices: XAUUSD, XAGUSD, Wall Street 30 (Sesión de Nueva York: Rango 13:00-13:30 UTC)

Causalidad estricta, spreads reales de Deriv MT5, SL > TP prioritario, Cap=1.
"""

import pickle
import numpy as np
import pandas as pd
from pathlib import Path

CACHE_DIR = Path("data/cache_msnr")

SESSION_INSTRUMENTS = {
    'EURUSD': ('LONDON', 7, 0, 7, 30),
    'GBPUSD': ('LONDON', 7, 0, 7, 30),
    'USDJPY': ('LONDON', 7, 0, 7, 30),
    'AUDNZD': ('LONDON', 7, 0, 7, 30),
    'XAUUSD': ('NY', 13, 0, 13, 30),
    'XAGUSD': ('NY', 13, 0, 13, 30),
    'Wall_Street_30': ('NY', 13, 0, 13, 30),
}

SPREADS = {
    'XAUUSD': 0.25, 'XAGUSD': 0.025, 'Wall_Street_30': 2.50,
    'EURUSD': 0.00015, 'GBPUSD': 0.00020, 'USDJPY': 0.018, 'AUDNZD': 0.00025
}

def wilson_interval(w, n, z=1.95996):
    if n == 0:
        return 0.0, 0.0
    p = w / n
    denom = 1 + (z**2) / n
    center = (p + (z**2) / (2 * n)) / denom
    spread = (z / denom) * np.sqrt((p * (1 - p) / n) + ((z**2) / (4 * (n**2))))
    return max(0.0, center - spread), min(1.0, center + spread)

def run_orb():
    all_signals = []
    
    for sym, (sess_name, h_start, m_start, h_end, m_end) in SESSION_INSTRUMENTS.items():
        p = CACHE_DIR / f"{sym}_M15.pkl"
        if not p.exists():
            continue
        with open(p, "rb") as f:
            df = pickle.load(f)
        df.columns = [c.lower() for c in df.columns]
        time_col = 'time' if 'time' in df.columns else 'datetime' if 'datetime' in df.columns else None
        if time_col:
            df['time'] = pd.to_datetime(df[time_col], utc=True)
        else:
            df['time'] = pd.to_datetime(df.index, utc=True)
        df = df.sort_values('time').reset_index(drop=True)
        
        spread = SPREADS.get(sym, 0.0001)
        
        # Agrupar por día
        df['date'] = df['time'].dt.date
        df['hour'] = df['time'].dt.hour
        df['minute'] = df['time'].dt.minute
        
        for date, group in df.groupby('date'):
            # Encontrar velas de apertura de rango (07:00 y 07:15, o 13:00 y 13:15)
            orb_bars = group[(group['hour'] == h_start) & (group['minute'].isin([0, 15]))]
            if len(orb_bars) < 2:
                continue
                
            orb_high = orb_bars['high'].max()
            orb_low = orb_bars['low'].min()
            orb_range = orb_high - orb_low
            
            if orb_range <= 0 or orb_range < 2.0 * spread:
                continue
                
            # Velas post-rango en la misma sesión (siguientes 4 horas)
            session_bars = group[group['time'] > orb_bars['time'].max()]
            if session_bars.empty:
                continue
                
            first_breakout = False
            for idx, bar in session_bars.iterrows():
                if first_breakout:
                    break
                # Solo evaluar dentro de las 3 horas siguientes al rango
                if (bar['time'] - orb_bars['time'].max()).total_seconds() > 3 * 3600:
                    break
                    
                # Breakout BUY
                if bar['close'] > orb_high:
                    first_breakout = True
                    entry_idx = df.index[df['time'] == bar['time']][0]
                    if entry_idx + 1 >= len(df):
                        break
                    entry_p = df['open'].iloc[entry_idx + 1] + spread
                    sl_p = orb_low # SL en el mínimo del rango
                    risk = entry_p - sl_p
                    if risk <= 0:
                        break
                    tp_p = entry_p + 1.5 * risk
                    
                    outcome = "LOSS"
                    rr = -1.0
                    exit_time = df['time'].iloc[min(entry_idx + 20, len(df)-1)]
                    for j in range(entry_idx + 1, min(entry_idx + 40, len(df))):
                        if df['low'].iloc[j] <= sl_p:
                            outcome = "LOSS"
                            rr = -1.0
                            exit_time = df['time'].iloc[j]
                            break
                        elif df['high'].iloc[j] >= tp_p:
                            outcome = "WIN"
                            rr = 1.5
                            exit_time = df['time'].iloc[j]
                            break
                    all_signals.append({
                        "symbol": sym, "direction": "BUY",
                        "entry_time": df['time'].iloc[entry_idx + 1],
                        "exit_time": exit_time, "outcome": outcome, "rr": rr
                    })
                    
                # Breakout SELL
                elif bar['close'] < orb_low:
                    first_breakout = True
                    entry_idx = df.index[df['time'] == bar['time']][0]
                    if entry_idx + 1 >= len(df):
                        break
                    entry_p = df['open'].iloc[entry_idx + 1] - spread
                    sl_p = orb_high
                    risk = sl_p - entry_p
                    if risk <= 0:
                        break
                    tp_p = entry_p - 1.5 * risk
                    
                    outcome = "LOSS"
                    rr = -1.0
                    exit_time = df['time'].iloc[min(entry_idx + 20, len(df)-1)]
                    for j in range(entry_idx + 1, min(entry_idx + 40, len(df))):
                        if df['high'].iloc[j] >= sl_p:
                            outcome = "LOSS"
                            rr = -1.0
                            exit_time = df['time'].iloc[j]
                            break
                        elif df['low'].iloc[j] <= tp_p:
                            outcome = "WIN"
                            rr = 1.5
                            exit_time = df['time'].iloc[j]
                            break
                    all_signals.append({
                        "symbol": sym, "direction": "SELL",
                        "entry_time": df['time'].iloc[entry_idx + 1],
                        "exit_time": exit_time, "outcome": outcome, "rr": rr
                    })
                    
    # Simular con Cap=1
    all_signals.sort(key=lambda x: x['entry_time'])
    executed = []
    active_until = None
    for s in all_signals:
        if active_until is not None and s['entry_time'] < active_until:
            continue
        executed.append(s)
        active_until = s['exit_time']
        
    df_ex = pd.DataFrame(executed)
    n = len(df_ex)
    wins = len(df_ex[df_ex['outcome'] == 'WIN'])
    losses = len(df_ex[df_ex['outcome'] == 'LOSS'])
    wr = (wins / n) * 100 if n > 0 else 0
    w_low, w_high = wilson_interval(wins, n)
    net_pnl = df_ex['rr'].sum()
    pf = (df_ex[df_ex['rr'] > 0]['rr'].sum() / abs(df_ex[df_ex['rr'] < 0]['rr'].sum())) if losses > 0 else 99
    
    # MaxDD
    equity = df_ex['rr'].cumsum()
    peak = equity.cummax()
    max_dd = (peak - equity).max()
    
    print("=" * 90)
    print("RESULTADOS OPENING RANGE BREAKOUT (ORB) EN METALES, INDICES Y FOREX")
    print("=" * 90)
    print(f"Total Operaciones (Cap=1): {n}")
    print(f"Wins / Losses: {wins}W / {losses}L")
    print(f"Win Rate: {wr:.1f}% (IC Wilson 95%: [{w_low*100:.1f}%, {w_high*100:.1f}%])")
    print(f"Net PnL: {net_pnl:+.2f} R")
    print(f"Expectativa: {net_pnl/n:+.4f} R/op")
    print(f"Profit Factor: {pf:.2f}")
    print(f"Max Drawdown: {max_dd:.2f} R")
    
    # Por activo
    print("\nDesglose por Activo:")
    for sym, grp in df_ex.groupby('symbol'):
        s_w = len(grp[grp['outcome'] == 'WIN'])
        s_l = len(grp[grp['outcome'] == 'LOSS'])
        s_pnl = grp['rr'].sum()
        s_pf = (grp[grp['rr'] > 0]['rr'].sum() / abs(grp[grp['rr'] < 0]['rr'].sum())) if s_l > 0 else 99
        print(f"  {sym:16s} | N={len(grp):3d} | WR={(s_w/len(grp))*100:5.1f}% | PnL={s_pnl:+7.2f}R | PF={s_pf:5.2f}")

if __name__ == '__main__':
    run_orb()
