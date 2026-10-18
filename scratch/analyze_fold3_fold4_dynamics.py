"""
scratch/analyze_fold3_fold4_dynamics.py
Análisis forense en profundidad de la dinámica de los Folds 3 y 4:
- ¿Por qué el Fold 3 se deteriora severamente en Var 3 (-71.4%)?
- ¿Por qué el Fold 4 permanece 100% idéntico (+0.00 R)?
- Trazabilidad exacta de cada operación en Folds 3 y 4.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pandas as pd
import numpy as np

from scratch.test_subfamily_and_filter_improvements import (
    evaluate_variant, get_subfamily, compute_detailed_kpis, eval_friction
)

def main():
    csv_path = Path("scratch/msnr_complete_23_faithful_trades_clean.csv")
    df = pd.read_csv(csv_path)
    df['time'] = pd.to_datetime(df['time'], utc=True)
    df['exit_time'] = pd.to_datetime(df['exit_time'], utc=True)
    df['subfamily'] = df['symbol'].apply(get_subfamily)
    df = df.sort_values('time').reset_index(drop=True)

    def f_v4(d):
        return d[(d['adx'] >= 30.0) & (d['risk_atr'] <= 1.5)]

    def f_var3(d):
        cond_strict = (d['subfamily'].isin(['FOREX', 'METALS'])) & (d['adx'] >= 30.0) & (d['risk_atr'] <= 1.2)
        cond_synth = (d['subfamily'] == 'SYNTH') & (d['adx'] >= 30.0) & (d['risk_atr'] <= 1.5)
        return d[cond_strict | cond_synth]

    r4 = evaluate_variant(df, f_v4, cap=1)
    r3 = evaluate_variant(df, f_var3, cap=1)

    t4 = r4['trades']
    t3 = r3['trades']

    print("=" * 115)
    print("ANÁLISIS FORENSE DE TRADES EN FOLD 3 (2026-07-31 a 2026-09-04)")
    print("=" * 115)
    f3_v4 = t4[(t4['time'] >= '2026-07-31 09:30') & (t4['time'] < '2026-09-04 15:00')].copy()
    f3_v3 = t3[(t3['time'] >= '2026-07-31 09:30') & (t3['time'] < '2026-09-04 15:00')].copy()

    print(f"V4 en Fold 3 (Total N={len(f3_v4)} ops):")
    for idx, r in f3_v4.iterrows():
        in_v3 = "SÍ (Conservada)" if len(f3_v3[(f3_v3['time']==r['time']) & (f3_v3['symbol']==r['symbol'])]) > 0 else "NO (ELIMINADA)"
        print(f"  {r['time'].strftime('%Y-%m-%d %H:%M')} | {r['symbol']:22s} | {r['direction']:4s} | ATR={r['risk_atr']:4.2f} | ADX={r['adx']:4.1f} | Outcome={r['outcome']:10s} | RR={r['rr']:+6.2f}R | ¿En Var3? {in_v3}")

    k4_f3 = compute_detailed_kpis(f3_v4['rr'], "Fold 3 V4")
    k3_f3 = compute_detailed_kpis(f3_v3['rr'], "Fold 3 Var3")
    print(f"\nResumen Fold 3:")
    print(f"  * V4 Baseline: N={k4_f3['n']} | WR={k4_f3['win_pct']:.1f}% | Net R={k4_f3['net_r']:+.2f}R | PF={k4_f3['pf']:.2f} | MaxDD={k4_f3['max_dd']:.2f}R")
    print(f"  * Variante 3:  N={k3_f3['n']} | WR={k3_f3['win_pct']:.1f}% | Net R={k3_f3['net_r']:+.2f}R | PF={k3_f3['pf']:.2f} | MaxDD={k3_f3['max_dd']:.2f}R")
    print(f"  * Contracción: Delta PnL = {k3_f3['net_r'] - k4_f3['net_r']:+.2f} R ({((k3_f3['net_r'] - k4_f3['net_r'])/k4_f3['net_r'])*100:.1f}%)")

    print("\n" + "=" * 115)
    print("ANÁLISIS FORENSE DE TRADES EN FOLD 4 (HOLDOUT INTACTO: 2026-09-04 a 2026-10-10)")
    print("=" * 115)
    f4_v4 = t4[t4['time'] >= '2026-09-04 15:00'].copy()
    f4_v3 = t3[t3['time'] >= '2026-09-04 15:00'].copy()

    print(f"V4 en Fold 4 (Total N={len(f4_v4)} ops):")
    for idx, r in f4_v4.iterrows():
        in_v3 = "SÍ (Conservada)" if len(f4_v3[(f4_v3['time']==r['time']) & (f4_v3['symbol']==r['symbol'])]) > 0 else "NO (ELIMINADA)"
        subfam = r['subfamily']
        print(f"  {r['time'].strftime('%Y-%m-%d %H:%M')} | {r['symbol']:25s} | {subfam:8s} | {r['direction']:4s} | ATR={r['risk_atr']:4.2f} | ADX={r['adx']:4.1f} | Outcome={r['outcome']:10s} | RR={r['rr']:+6.2f}R | ¿En Var3? {in_v3}")

    k4_f4 = compute_detailed_kpis(f4_v4['rr'], "Fold 4 V4")
    k3_f4 = compute_detailed_kpis(f4_v3['rr'], "Fold 4 Var3")
    print(f"\nResumen Fold 4 (Holdout Intacto):")
    print(f"  * V4 Baseline: N={k4_f4['n']} | WR={k4_f4['win_pct']:.1f}% | Net R={k4_f4['net_r']:+.2f}R | PF={k4_f4['pf']:.2f} | MaxDD={k4_f4['max_dd']:.2f}R")
    print(f"  * Variante 3:  N={k3_f4['n']} | WR={k3_f4['win_pct']:.1f}% | Net R={k3_f4['net_r']:+.2f}R | PF={k3_f4['pf']:.2f} | MaxDD={k3_f4['max_dd']:.2f}R")
    print(f"  * Variación:   Delta PnL = {k3_f4['net_r'] - k4_f4['net_r']:+.2f} R (0.0% de cambio, neutralidad absoluta)")

if __name__ == '__main__':
    main()
