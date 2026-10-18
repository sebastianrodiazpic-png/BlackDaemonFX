"""
scratch/audit_cap1_order_sensitivity.py
Auditoría rigurosa de sensibilidad al orden de procesamiento y desempate en Cap=1.
Analiza todas las señales simultáneas (mismo timestamp de entrada) en Malaysian SNR V2 (ADX>=30 + ATR<=1.5)
y comprueba si alterar el orden de símbolos o invertir la prioridad modifica las métricas finales.
"""

import sys
from pathlib import Path
import pandas as pd
import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from strategy.malaysian_snr.config import MalaysianSNRConfig

def simulate_cap1_with_order(trades_df: pd.DataFrame, sort_key=None, reverse_ties=False) -> pd.DataFrame:
    # If reverse_ties is True, sort simultaneous timestamps in reverse symbol order
    if reverse_ties:
        df_sorted = trades_df.sort_values(by=['time', 'symbol'], ascending=[True, False]).reset_index(drop=True)
    else:
        df_sorted = trades_df.sort_values(by=['time', 'symbol'], ascending=[True, True]).reset_index(drop=True)
        
    accepted = []
    open_positions = []
    for idx, row in df_sorted.iterrows():
        t_entry = row['time']
        open_positions = [t_exit for t_exit in open_positions if t_exit > t_entry]
        if len(open_positions) < 1:
            accepted.append(row)
            open_positions.append(row['exit_time'])
    return pd.DataFrame(accepted)

def compute_kpis(series: pd.Series) -> dict:
    n = len(series)
    if n == 0:
        return {"n": 0, "win_pct": 0.0, "net_r": 0.0, "exp_r": 0.0, "pf": 0.0, "max_dd": 0.0}
    w = series[series > 0.001]
    l = series[series < -0.001]
    nw = len(w)
    wr = nw / n * 100.0
    net_r = float(series.sum())
    exp_r = float(series.mean())
    tot_g = float(w.sum()) if nw > 0 else 0.0
    tot_l = float(abs(l.sum())) if len(l) > 0 else 0.0
    pf = (tot_g / tot_l) if tot_l > 0 else (99.0 if tot_g > 0 else 0.0)
    cum = series.cumsum()
    dd = cum.cummax() - cum
    max_dd = float(dd.max()) if len(dd) > 0 else 0.0
    return {
        "n": n, "win_pct": round(wr, 1), "net_r": round(net_r, 2),
        "exp_r": round(exp_r, 4), "pf": round(pf, 2), "max_dd": round(max_dd, 2)
    }

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

    all_v2 = []
    all_v4_asc = []
    all_v4_desc = []

    for f in range(n_folds):
        train_end = start_train + f * step
        test_end = min(total, train_end + step)
        
        split_time = df['time'].iloc[train_end]
        train_slice = df.iloc[:train_end]
        closed_mask = train_slice['exit_time'] < split_time
        train_clean = train_slice[closed_mask]
        
        test_slice = df.iloc[train_end:test_end].copy().reset_index(drop=True)
        sym_pnl = train_clean.groupby('symbol')['rr'].sum()
        pos_syms = set(sym_pnl[sym_pnl > 0].index)
        
        test_causal = test_slice[test_slice['symbol'].isin(pos_syms)].copy()
        v2 = test_causal[(test_causal['adx'] >= 30.0) & (test_causal['risk_atr'] <= 1.5)].copy().reset_index(drop=True)
        
        v4_asc = simulate_cap1_with_order(v2, reverse_ties=False)
        v4_desc = simulate_cap1_with_order(v2, reverse_ties=True)
        
        all_v2.append(v2)
        all_v4_asc.append(v4_asc)
        all_v4_desc.append(v4_desc)

    df_v2 = pd.concat(all_v2, ignore_index=True)
    df_v4_asc = pd.concat(all_v4_asc, ignore_index=True)
    df_v4_desc = pd.concat(all_v4_desc, ignore_index=True)

    print("=" * 100)
    print("AUDITORÍA DE SENSIBILIDAD AL ORDEN EN CAP=1 (SEÑALES SIMULTÁNEAS)")
    print("=" * 100)
    
    k_v2 = compute_kpis(df_v2['rr'])
    k_asc = compute_kpis(df_v4_asc['rr'])
    k_desc = compute_kpis(df_v4_desc['rr'])

    print(f"1. Sin Cap=1 (V2):         N={k_v2['n']:2d} | WR: {k_v2['win_pct']:4.1f}% | Net: {k_v2['net_r']:+6.2f} R | Exp: {k_v2['exp_r']:+6.4f} R | PF: {k_v2['pf']:4.2f} | MaxDD: {k_v2['max_dd']:4.2f} R")
    print(f"2. Con Cap=1 (Orden A-Z):  N={k_asc['n']:2d} | WR: {k_asc['win_pct']:4.1f}% | Net: {k_asc['net_r']:+6.2f} R | Exp: {k_asc['exp_r']:+6.4f} R | PF: {k_asc['pf']:4.2f} | MaxDD: {k_asc['max_dd']:4.2f} R")
    print(f"3. Con Cap=1 (Orden Z-A):  N={k_desc['n']:2d} | WR: {k_desc['win_pct']:4.1f}% | Net: {k_desc['net_r']:+6.2f} R | Exp: {k_desc['exp_r']:+6.4f} R | PF: {k_desc['pf']:4.2f} | MaxDD: {k_desc['max_dd']:4.2f} R")

    # Inspect simultaneous signals in V2
    time_counts = df_v2['time'].value_counts()
    simultaneous_times = time_counts[time_counts > 1].index

    print(f"\nNúmero de eventos simultáneos con >1 señal: {len(simultaneous_times)}")
    for t in simultaneous_times:
        sub = df_v2[df_v2['time'] == t]
        print(f"\nEvento Simultáneo en {t}:")
        for idx, row in sub.iterrows():
            print(f"  • {row['symbol']:20s} | Dir: {row['direction']:4s} | Entrada: {row['time']} | Salida: {row['exit_time']} | RR: {row['rr']:+.2f} R")

    print("\nSensibilidad al orden:")
    if k_asc == k_desc:
        print("  -> SENSIBILIDAD NULA: Cambiar el orden de desempate produce idéntico PnL, WinRate, PF y Drawdown.")
    else:
        print("  -> SENSIBILIDAD EXISTENTE: Los resultados varían según el orden de procesamiento.")

if __name__ == '__main__':
    main()
