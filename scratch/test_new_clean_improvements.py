"""
scratch/test_new_clean_improvements.py
Evaluación rigurosa de nuevas mejoras potenciales de una en una:
1. Baseline: V4 canónico (ADX >= 30, ATR <= 1.5, Cap=1)
2. Mejora A: Poda preventiva de Crash 1000 Index (por vulnerabilidad comprobada a fricción/gaps)
3. Mejora B: Exclusión de ventana de rollover nocturno (21:00 - 23:59 UTC) en Forex y Metales
4. Mejora C: Filtro de confirmación de quiebre (Body Ratio >= 0.50 en Forex y Metales)
5. Mejora D: Combinación Causal A + B (Poda Crash 1000 + Filtro Rollover Forex/Metales)

Walk-Forward de 4 Folds cronológico con purga y embargo estricto sobre 957 trades limpios.
"""

import sys
from pathlib import Path
import pandas as pd
import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Windows UTF-8
for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

from strategy.malaysian_snr.config import MalaysianSNRConfig
from scratch.test_subfamily_and_filter_improvements import (
    evaluate_variant, get_subfamily, wilson_score_interval,
    compute_detailed_kpis, eval_friction
)

def main():
    csv_path = PROJECT_ROOT / "scratch" / "msnr_complete_23_faithful_trades_clean.csv"
    df = pd.read_csv(csv_path)
    df['time'] = pd.to_datetime(df['time'], utc=True)
    df['exit_time'] = pd.to_datetime(df['exit_time'], utc=True)
    df['subfamily'] = df['symbol'].apply(get_subfamily)
    df = df.sort_values('time').reset_index(drop=True)

    # 1. Baseline V4
    def f_v4(d):
        return d[(d['adx'] >= 30.0) & (d['risk_atr'] <= 1.5)]

    # 2. Mejora A: Poda de Crash 1000 Index
    def f_prune_crash(d):
        base = (d['adx'] >= 30.0) & (d['risk_atr'] <= 1.5)
        not_crash = d['symbol'] != 'Crash 1000 Index'
        return d[base & not_crash]

    # 3. Mejora B: Exclusión de Rollover Nocturno (21:00 - 23:59 UTC) en Forex y Metales
    def f_no_rollover(d):
        base = (d['adx'] >= 30.0) & (d['risk_atr'] <= 1.5)
        # hour_utc outside [21, 22, 23] for forex/metals
        is_synth = d['subfamily'] == 'SYNTH'
        not_rollover = ~d['hour_utc'].isin([21, 22, 23])
        return d[base & (is_synth | not_rollover)]

    # 4. Mejora C: Body Ratio >= 0.50 en Forex y Metales
    def f_body_fx_met(d):
        base = (d['adx'] >= 30.0) & (d['risk_atr'] <= 1.5)
        is_synth = d['subfamily'] == 'SYNTH'
        good_body = d['body_ratio'] >= 0.50
        return d[base & (is_synth | good_body)]

    # 5. Mejora D: Poda Crash 1000 + Filtro Rollover
    def f_combined_safe(d):
        base = (d['adx'] >= 30.0) & (d['risk_atr'] <= 1.5)
        not_crash = d['symbol'] != 'Crash 1000 Index'
        is_synth = d['subfamily'] == 'SYNTH'
        not_rollover = ~d['hour_utc'].isin([21, 22, 23])
        return d[base & not_crash & (is_synth | not_rollover)]

    cands = [
        ("V4 Baseline (ADX>=30, ATR<=1.5, Cap=1)", f_v4),
        ("Mejora A: Poda Preventiva Crash 1000", f_prune_crash),
        ("Mejora B: Anti-Rollover Forex/Metales (21-23h)", f_no_rollover),
        ("Mejora C: Body Ratio >= 0.50 Forex/Metales", f_body_fx_met),
        ("Mejora D: Poda Crash 1000 + Anti-Rollover", f_combined_safe),
    ]

    print("=" * 125)
    print("EVALUACIÓN SISTEMÁTICA DE NUEVAS MEJORAS CANDIDATAS (WALK-FORWARD 4 FOLDS, 957 TRADES)")
    print("=" * 125)

    headers = ["Variante", "N", "Win%", "IC Wilson 95%", "Payoff", "Exp (R)", "Net PnL", "PF", "MaxDD", "Holdout R", "Fric.Mod R"]
    print(f"{headers[0]:42s} | {headers[1]:3s} | {headers[2]:5s} | {headers[3]:15s} | {headers[4]:6s} | {headers[5]:8s} | {headers[6]:8s} | {headers[7]:5s} | {headers[8]:6s} | {headers[9]:9s} | {headers[10]:10s}")
    print("-" * 135)

    results = {}
    for name, f_rule in cands:
        res = evaluate_variant(df, f_rule, cap=1, n_folds=4)
        k = res['k_tot']
        h = res['k_holdout']
        m = res['k_mod']
        results[name] = res
        print(f"{name:42s} | {k['n']:3d} | {k['win_pct']:4.1f}% | {k['ci_95']:15s} | {k['payoff']:6.2f} | {k['exp_r']:+7.4f}R | {k['net_r']:+7.2f}R | {k['pf']:5.2f} | {k['max_dd']:5.2f}R | {h['net_r']:+8.2f}R | {m['net_r']:+9.2f}R")

    print("\n" + "=" * 125)
    print("DESGLOSE POR FOLD DE CADA MEJORA CANDIDATA:")
    print("=" * 125)
    for name, res in results.items():
        print(f"\n--- {name} ---")
        for i in range(4):
            f_res = res['folds'][i]
            print(f"  Fold {i+1}: N={f_res['n']:2d} | W={f_res['n_win']:2d}, L={f_res['n_loss']:2d} | WR={f_res['win_pct']:5.1f}% | Net={f_res['net_r']:+6.2f}R | PF={f_res['pf']:5.2f} | MaxDD={f_res['max_dd']:4.2f}R")

if __name__ == '__main__':
    main()
