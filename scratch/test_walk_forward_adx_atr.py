"""
scratch/test_walk_forward_adx_atr.py
Evaluación walk-forward de 4 folds con purga y embargo para:
1. Base Causal ADX >= 30
2. Base Causal ADX >= 30 + ATR <= 1.5
3. Base Causal ADX >= 30 + Concurrencia = 1
4. Base Causal ADX >= 30 + ATR <= 1.5 + Concurrencia = 1
"""

import pandas as pd
import numpy as np
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from strategy.malaysian_snr.config import MalaysianSNRConfig

def simulate_concurrency_cap(trades_df: pd.DataFrame, max_open: int = 1) -> pd.DataFrame:
    accepted = []
    open_positions = []
    for idx, row in trades_df.iterrows():
        t_entry = row['time']
        open_positions = [t_exit for t_exit in open_positions if t_exit > t_entry]
        if len(open_positions) < max_open:
            accepted.append(row)
            open_positions.append(row['exit_time'])
    return pd.DataFrame(accepted)

def compute_pf(series: pd.Series) -> float:
    w = series[series > 0.001].sum()
    l = abs(series[series < -0.001].sum())
    return round(float(w / l), 2) if l > 0 else (99.0 if w > 0 else 0.0)

def main():
    df = pd.read_csv(PROJECT_ROOT / 'storage' / 'analysis' / 'msnr_faithful_trades.csv')
    df['time'] = pd.to_datetime(df['time'], utc=True)
    df = df.sort_values('time').reset_index(drop=True)
    df['exit_time'] = df['time'] + pd.to_timedelta(df['bars'] * 15, unit='m')

    cfg = MalaysianSNRConfig()
    allowed = set(s.replace('micro', '') for s in cfg.allowed_symbols)
    df = df[df['symbol'].isin(allowed)].reset_index(drop=True)

    total = len(df)
    n_folds = 4
    start_train = total // (n_folds + 1)
    step = (total - start_train) // n_folds

    print("=" * 115)
    print("EVALUACIÓN WALK-FORWARD DE 4 FOLDS: ROBUSTEZ TEMPORAL DE FILTROS EX ANTE")
    print("=" * 115)

    all_v1, all_v2, all_v3, all_v4 = [], [], [], []

    for f in range(n_folds):
        train_end = start_train + f * step
        test_end = min(total, train_end + step)
        
        split_time = df['time'].iloc[train_end]
        train_slice = df.iloc[:train_end]
        closed_mask = train_slice['exit_time'] < split_time
        train_clean = train_slice[closed_mask]
        
        test_slice = df.iloc[train_end:test_end].copy().reset_index(drop=True)
        
        # Causal asset selection: symbols with sum(rr) > 0 in train_clean
        sym_pnl = train_clean.groupby('symbol')['rr'].sum()
        pos_syms = set(sym_pnl[sym_pnl > 0].index)
        
        test_causal = test_slice[test_slice['symbol'].isin(pos_syms)].copy()
        
        # V1: ADX >= 30
        v1 = test_causal[test_causal['adx'] >= 30.0].copy().reset_index(drop=True)
        # V2: ADX >= 30 + ATR <= 1.5
        v2 = test_causal[(test_causal['adx'] >= 30.0) & (test_causal['risk_atr'] <= 1.5)].copy().reset_index(drop=True)
        # V3: ADX >= 30 + Concurrency = 1
        v3 = simulate_concurrency_cap(v1, max_open=1) if len(v1) > 0 else pd.DataFrame()
        # V4: ADX >= 30 + ATR <= 1.5 + Concurrency = 1
        v4 = simulate_concurrency_cap(v2, max_open=1) if len(v2) > 0 else pd.DataFrame()
        
        all_v1.append(v1)
        all_v2.append(v2)
        all_v3.append(v3)
        all_v4.append(v4)
        
        print(f"\n--- FOLD {f+1}: Train N={len(train_clean)} ({len(pos_syms)} pos assets) | Test OOS N={len(test_slice)} ---")
        for vname, vdf in [("1. ADX >= 30", v1), ("2. ADX >= 30 + ATR <= 1.5", v2), 
                           ("3. ADX >= 30 + Cap=1", v3), ("4. ADX >= 30 + ATR<=1.5 + Cap=1", v4)]:
            if len(vdf) > 0:
                n = len(vdf)
                wr = (vdf['rr'] > 0).mean() * 100
                net = vdf['rr'].sum()
                exp = vdf['rr'].mean()
                pf = compute_pf(vdf['rr'])
                print(f"  {vname:34s} | N={n:2d} | WR: {wr:4.1f}% | Net R: {net:+6.2f} R | Exp: {exp:+6.4f} R | PF: {pf:4.2f}")
            else:
                print(f"  {vname:34s} | N= 0 | Sin operaciones")

    print("\n" + "=" * 115)
    print("RESUMEN GLOBAL ACUMULADO WALK-FORWARD (OOS CONGELADO EN CADA VENTANA)")
    print("=" * 115)
    df_v1 = pd.concat(all_v1, ignore_index=True) if len(all_v1) > 0 else pd.DataFrame()
    df_v2 = pd.concat(all_v2, ignore_index=True) if len(all_v2) > 0 else pd.DataFrame()
    df_v3 = pd.concat(all_v3, ignore_index=True) if len(all_v3) > 0 else pd.DataFrame()
    df_v4 = pd.concat(all_v4, ignore_index=True) if len(all_v4) > 0 else pd.DataFrame()

    for vname, vdf in [("1. ADX >= 30", df_v1), ("2. ADX >= 30 + ATR <= 1.5", df_v2), 
                       ("3. ADX >= 30 + Cap=1", df_v3), ("4. ADX >= 30 + ATR<=1.5 + Cap=1", df_v4)]:
        n = len(vdf)
        wr = (vdf['rr'] > 0).mean() * 100
        net = vdf['rr'].sum()
        exp = vdf['rr'].mean()
        pf = compute_pf(vdf['rr'])
        cum = vdf['rr'].cumsum()
        max_dd = round(float((cum.cummax() - cum).max()), 2) if len(cum) > 0 else 0.0
        print(f"  {vname:34s} | N={n:3d} | WR: {wr:4.1f}% | Net R: {net:+6.2f} R | Exp: {exp:+6.4f} R | PF: {pf:4.2f} | MaxDD: {max_dd:5.2f} R")

    print("\n" + "=" * 115)
    print("SENSIBILIDAD A FRICCIÓN ACUMULADA WALK-FORWARD (4 FOLDS)")
    print("=" * 115)
    for vname, vdf in [("ADX >= 30 (N=70)", df_v1), ("ADX >= 30 + ATR <= 1.5 (N=43)", df_v2), 
                       ("ADX >= 30 + Cap=1 (N=59)", df_v3), ("ADX >= 30 + ATR<=1.5 + Cap=1 (N=39)", df_v4)]:
        print(f"\n  >>> VARIANTE: {vname}")
        for sname, slip_r, gap_pct in [("Base (Spread Real)", 0.0, 0.0),
                                       ("Fricción Baja (+0.025R / 10% gap)", 0.025, 0.10),
                                       ("Fricción Moderada (+0.05R / 15% gap)", 0.05, 0.15),
                                       ("Fricción Severa (+0.10R / 20% gap)", 0.10, 0.20)]:
            rr = vdf['rr'].copy()
            if slip_r > 0: rr -= slip_r
            if gap_pct > 0:
                l = rr < 0
                rr[l] -= abs(rr[l]) * gap_pct
            net = rr.sum()
            exp = rr.mean()
            pf = compute_pf(rr)
            cum = rr.cumsum()
            dd = round(float((cum.cummax() - cum).max()), 2) if len(cum) > 0 else 0.0
            print(f"    {sname:38s} | Net R: {net:+6.2f} R | Exp: {exp:+6.4f} R | PF: {pf:4.2f} | MaxDD: {dd:5.2f} R")

if __name__ == '__main__':
    main()
