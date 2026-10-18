"""
scratch/run_controlled_ablations.py
Ablaciones controladas de filtros individuales y combinaciones sobre el dataset limpio de 957 trades.
Walk-Forward cronológico de 4 folds con purga y embargo estricto. Holdout intacto (Fold 4).
"""

import sys
from pathlib import Path
import pandas as pd
import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from scratch.test_subfamily_and_filter_improvements import (
    evaluate_variant, get_subfamily, wilson_score_interval, compute_detailed_kpis
)

def main():
    csv_path = PROJECT_ROOT / "scratch" / "msnr_complete_23_faithful_trades_clean.csv"
    df = pd.read_csv(csv_path)
    df['time'] = pd.to_datetime(df['time'], utc=True)
    df['exit_time'] = pd.to_datetime(df['exit_time'], utc=True)
    df['subfamily'] = df['symbol'].apply(get_subfamily)
    df = df.sort_values('time').reset_index(drop=True)

    # 1. Definición de filtros para ablaciones
    # Benchmark V4
    def f_v4(d):
        return d[(d['adx'] >= 30.0) & (d['risk_atr'] <= 1.5)]

    # Filtro individual A: ATR <= 1.2 solo en Metales (Forex y Sintéticos en 1.5)
    def f_atr_metals_only(d):
        cond_metals = (d['subfamily'] == 'METALS') & (d['adx'] >= 30.0) & (d['risk_atr'] <= 1.2)
        cond_other = (d['subfamily'] != 'METALS') & (d['adx'] >= 30.0) & (d['risk_atr'] <= 1.5)
        return d[cond_metals | cond_other]

    # Filtro individual B: ATR <= 1.2 solo en Forex (Metales y Sintéticos en 1.5)
    def f_atr_forex_only(d):
        cond_forex = (d['subfamily'] == 'FOREX') & (d['adx'] >= 30.0) & (d['risk_atr'] <= 1.2)
        cond_other = (d['subfamily'] != 'FOREX') & (d['adx'] >= 30.0) & (d['risk_atr'] <= 1.5)
        return d[cond_forex | cond_other]

    # Variante Experimental: ATR <= 1.2 en Forex y Metales
    def f_atr_forex_metals(d):
        cond_strict = (d['subfamily'].isin(['FOREX', 'METALS'])) & (d['adx'] >= 30.0) & (d['risk_atr'] <= 1.2)
        cond_synth = (d['subfamily'] == 'SYNTH') & (d['adx'] >= 30.0) & (d['risk_atr'] <= 1.5)
        return d[cond_strict | cond_synth]

    # Combinación C: ATR <= 1.2 en Forex y Metales + Body Ratio >= 0.50 en Sintéticos
    def f_comb_body50(d):
        cond_strict = (d['subfamily'].isin(['FOREX', 'METALS'])) & (d['adx'] >= 30.0) & (d['risk_atr'] <= 1.2)
        cond_synth = (d['subfamily'] == 'SYNTH') & (d['adx'] >= 30.0) & (d['risk_atr'] <= 1.5) & (d['body_ratio'] >= 0.50)
        return d[cond_strict | cond_synth]

    # Combinación D: ATR <= 1.2 en Forex y Metales + ADX >= 35 en Sintéticos
    def f_comb_adx35_synth(d):
        cond_strict = (d['subfamily'].isin(['FOREX', 'METALS'])) & (d['adx'] >= 30.0) & (d['risk_atr'] <= 1.2)
        cond_synth = (d['subfamily'] == 'SYNTH') & (d['adx'] >= 35.0) & (d['risk_atr'] <= 1.5)
        return d[cond_strict | cond_synth]

    ablations = [
        ("Benchmark V4 (ADX>=30, ATR<=1.5, Cap=1)", f_v4, 1),
        ("Ablación 1: ATR<=1.2 Solo en Metales", f_atr_metals_only, 1),
        ("Ablación 2: ATR<=1.2 Solo en Forex", f_atr_forex_only, 1),
        ("Variante ATR: ATR<=1.2 Metales + Forex", f_atr_forex_metals, 1),
        ("Combinación 1: Var ATR + Sintéticos Body>=0.50", f_comb_body50, 1),
        ("Combinación 2: Var ATR + Sintéticos ADX>=35", f_comb_adx35_synth, 1),
    ]

    print("=" * 135)
    print("ABLACIONES CONTROLADAS Y COMBINACIONES SOBRE EL UNIVERSO CANÓNICO (WALK-FORWARD 4 FOLDS)")
    print("=" * 135)
    print(f"{'Configuración / Ablación':46s} | {'N':3s} | {'Win%':5s} | {'IC Wilson 95%':16s} | {'Payoff':6s} | {'Exp (R)':8s} | {'Net R':8s} | {'PF':5s} | {'MaxDD':6s} | {'Holdout R':9s} | {'Fric.Mod':8s}")
    print("-" * 135)

    results = {}
    for name, f_func, cap in ablations:
        res = evaluate_variant(df, f_func, cap=cap, n_folds=4)
        results[name] = res
        k = res['k_tot']
        kh = res['k_holdout']
        km = res['k_mod']
        print(f"{name:46s} | {k['n']:3d} | {k['win_pct']:4.1f}% | {k['ci_95']:16s} | {k['payoff']:6.2f} | {k['exp_r']:+7.4f}R | {k['net_r']:+7.2f}R | {k['pf']:5.2f} | {k['max_dd']:5.2f}R | {kh['net_r']:+8.2f}R | {km['net_r']:+7.2f}R")

    print("\n" + "=" * 135)
    print("ESTABILIDAD POR FOLD DE CADA ABLACIÓN")
    print("=" * 135)
    for name, res in results.items():
        print(f"\n--- {name} ---")
        for i, fk in enumerate(res['folds']):
            print(f"  Fold {i+1}: N={fk['n']:2d} | W={fk['n_win']:2d}, L={fk['n_loss']:2d} | Win%: {fk['win_pct']:4.1f}% | Net R: {fk['net_r']:+6.2f}R | Exp: {fk['exp_r']:+6.4f}R | PF: {fk['pf']:4.2f} | MaxDD: {fk['max_dd']:4.2f}R")

if __name__ == '__main__':
    main()
