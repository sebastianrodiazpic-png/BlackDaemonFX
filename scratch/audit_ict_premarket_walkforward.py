"""
scratch/audit_ict_premarket_walkforward.py
Evaluación del bloqueo 07:00 - 09:00 NY en ICT a través de 3 ventanas temporales independientes.
"""

import sys
from pathlib import Path
import pandas as pd
import numpy as np
from zoneinfo import ZoneInfo

PROJECT_ROOT = Path(__file__).resolve().parent.parent

def compute_metrics(series: pd.Series) -> dict:
    n = len(series)
    if n == 0:
        return {"n": 0, "win_pct": 0.0, "net_r": 0.0, "exp_r": 0.0, "pf": 0.0, "max_dd": 0.0}
    wins = series[series > 0.001]
    losses = series[series < -0.001]
    nw = len(wins)
    wr = nw / n * 100.0
    net_r = float(series.sum())
    exp_r = float(series.mean())
    tot_g = float(wins.sum()) if nw > 0 else 0.0
    tot_l = float(abs(losses.sum())) if len(losses) > 0 else 0.0
    pf = (tot_g / tot_l) if tot_l > 0 else (99.0 if tot_g > 0 else 0.0)
    cum = series.cumsum()
    dd = cum.cummax() - cum
    max_dd = float(dd.max()) if len(dd) > 0 else 0.0
    return {
        "n": n, "win_pct": round(wr, 1), "net_r": round(net_r, 2),
        "exp_r": round(exp_r, 4), "pf": round(pf, 2), "max_dd": round(max_dd, 2)
    }

def main():
    df = pd.read_csv(PROJECT_ROOT / 'storage' / 'analysis' / 'ict_faithful_trades.csv')
    time_col = [c for c in df.columns if 'time' in c.lower() or 'date' in c.lower()][0]
    df['time_utc'] = pd.to_datetime(df[time_col], utc=True)
    df = df.sort_values('time_utc').reset_index(drop=True)
    
    ny_tz = ZoneInfo("America/New_York")
    df['time_ny'] = df['time_utc'].dt.tz_convert(ny_tz)
    df['time_ny_float'] = df['time_ny'].dt.hour + df['time_ny'].dt.minute / 60.0
    
    premarket_mask = (df['time_ny_float'] >= 7.0) & (df['time_ny_float'] < 9.0)
    df_filtered = df[~premarket_mask].copy().reset_index(drop=True)
    
    print("=" * 100)
    print("AUDITORÍA DE ROBUSTEZ: BLOQUEO PRE-MARKET (07:00 - 09:00 NY) EN ICT EN 3 VENTANAS")
    print("=" * 100)
    
    n_total = len(df_filtered)
    step = n_total // 3
    for w in range(3):
        start = w * step
        end = (w + 1) * step if w < 2 else n_total
        sub_w = df_filtered.iloc[start:end]
        kw = compute_metrics(sub_w['rr'])
        
        # compare with base in same window
        base_w = df[(df['time_utc'] >= sub_w['time_utc'].min()) & (df['time_utc'] <= sub_w['time_utc'].max())]
        k_base = compute_metrics(base_w['rr'])
        
        d_start = sub_w['time_utc'].min().strftime('%Y-%m-%d')
        d_end = sub_w['time_utc'].max().strftime('%Y-%m-%d')
        print(f"\nVentana {w+1} ({d_start} a {d_end}):")
        print(f"  Base ICT          : N={k_base['n']:3d} | Net: {k_base['net_r']:+6.2f} R | Exp: {k_base['exp_r']:+6.4f} R | PF: {k_base['pf']:4.2f} | MaxDD: {k_base['max_dd']:4.2f} R")
        print(f"  Bloqueo Pre-Market: N={kw['n']:3d} | Net: {kw['net_r']:+6.2f} R | Exp: {kw['exp_r']:+6.4f} R | PF: {kw['pf']:4.2f} | MaxDD: {kw['max_dd']:4.2f} R")

if __name__ == '__main__':
    main()
