"""
scratch/audit_ict_london_session_walkforward.py
Evaluación de la sesión de Londres (02:00 - 05:00 NY) de ICT a través de ventanas
temporales independientes (walk-forward) y por activo, para comprobar si los +25.66 R
son estables o producto de un régimen temporal concentrado.
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
    
    # London filter: 02:00 to 05:00 NY
    london_mask = (df['time_ny_float'] >= 2.0) & (df['time_ny_float'] < 5.0)
    df_london = df[london_mask].copy().reset_index(drop=True)
    
    print("=" * 100)
    print("AUDITORÍA DE ROBUSTEZ: SESIÓN DE LONDRES ICT (02:00 - 05:00 NY)")
    print("=" * 100)
    
    k_tot = compute_metrics(df_london['rr'])
    print(f"Muestra Total Londres: N={k_tot['n']} | WR: {k_tot['win_pct']}% | Net: {k_tot['net_r']:+.2f} R | Exp: {k_tot['exp_r']:+.4f} R | PF: {k_tot['pf']} | MaxDD: {k_tot['max_dd']} R")
    
    # Temporal validation: Split into 3 independent chronological windows
    n_total = len(df_london)
    step = n_total // 3
    print("\n1. DESGLOSE POR VENTANAS TEMPORALES INDEPENDIENTES (3 PARTES):")
    for w in range(3):
        start = w * step
        end = (w + 1) * step if w < 2 else n_total
        sub_w = df_london.iloc[start:end]
        kw = compute_metrics(sub_w['rr'])
        d_start = sub_w['time_utc'].min().strftime('%Y-%m-%d')
        d_end = sub_w['time_utc'].max().strftime('%Y-%m-%d')
        print(f"  Ventana {w+1} ({d_start} a {d_end}): N={kw['n']:2d} | WR: {kw['win_pct']:4.1f}% | Net: {kw['net_r']:+6.2f} R | Exp: {kw['exp_r']:+6.4f} R | PF: {kw['pf']:4.2f} | MaxDD: {kw['max_dd']:4.2f} R")
        
    # Breakdown by Asset
    print("\n2. DESGLOSE POR ACTIVO EN SESIÓN DE LONDRES (Top activos por volumen/PnL):")
    asset_grp = df_london.groupby('symbol')['rr'].agg(
        trades='count', wins=lambda x: (x > 0).sum(), net_r='sum'
    ).sort_values('net_r', ascending=False)
    
    for sym, row in asset_grp.iterrows():
        tr = int(row['trades'])
        w = int(row['wins'])
        net = float(row['net_r'])
        wr = w / tr * 100.0 if tr > 0 else 0.0
        sub_s = df_london[df_london['symbol'] == sym]['rr']
        ks = compute_metrics(sub_s)
        print(f"  {sym:25s} | N={tr:2d} (W={w:2d}) | WR: {wr:4.1f}% | Net: {net:+6.2f} R | Exp: {ks['exp_r']:+6.4f} R | PF: {ks['pf']:4.2f} | MaxDD: {ks['max_dd']:4.2f} R")

if __name__ == '__main__':
    main()
