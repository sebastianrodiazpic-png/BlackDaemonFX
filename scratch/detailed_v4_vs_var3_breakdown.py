"""
scratch/detailed_v4_vs_var3_breakdown.py
Comparación exhaustiva y reproducible: V4 Baseline vs. Variante 3 (Metales/Forex ATR <= 1.2)
- Desglose por activo, dirección, fold y ventana temporal.
- Desglose de señales descartadas y añadidas por Cap=1.
- Métricas con intervalos de confianza de Wilson al 95%.
- Evaluación bajo fricción moderada y severa.
- Análisis de estabilidad y riesgo de sobreajuste.
"""

import sys
from pathlib import Path
import pandas as pd
import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

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

    # 1. Definición de filtros
    def f_v4(d):
        return d[(d['adx'] >= 30.0) & (d['risk_atr'] <= 1.5)]

    def f_var3(d):
        cond_strict = (d['subfamily'].isin(['FOREX', 'METALS'])) & (d['adx'] >= 30.0) & (d['risk_atr'] <= 1.2)
        cond_synth = (d['subfamily'] == 'SYNTH') & (d['adx'] >= 30.0) & (d['risk_atr'] <= 1.5)
        return d[cond_strict | cond_synth]

    res_v4 = evaluate_variant(df, f_v4, cap=1, n_folds=4)
    res_v3 = evaluate_variant(df, f_var3, cap=1, n_folds=4)

    t_v4 = res_v4['trades'].copy()
    t_v3 = res_v3['trades'].copy()

    cfg = MalaysianSNRConfig()
    canonical_symbols = sorted(list(set(s.replace('micro', '') for s in cfg.allowed_symbols)))

    print("=" * 125)
    print("COMPARACIÓN DETALLADA: V4 BASELINE vs. VARIANTE 3 (METALES/FOREX ATR <= 1.2)")
    print("=" * 125)

    k_v4 = res_v4['k_tot']
    k_v3 = res_v3['k_tot']

    print(f"\n1. RESUMEN MAESTRO GLOBAL:")
    print(f"{'Métrica':25s} | {'V4 Baseline':20s} | {'Var 3 (ATR<=1.2)':20s} | {'Diferencia (Var3 - V4)'}")
    print("-" * 85)
    print(f"{'Operaciones (N)':25s} | {k_v4['n']:20d} | {k_v3['n']:20d} | {k_v3['n'] - k_v4['n']:+d} ops")
    wlb_v4 = f"{k_v4['n_win']}W / {k_v4['n_loss']}L / {k_v4['n_be']}BE"
    wlb_v3 = f"{k_v3['n_win']}W / {k_v3['n_loss']}L / {k_v3['n_be']}BE"
    print(f"{'Wins / Losses / BE':25s} | {wlb_v4:20s} | {wlb_v3:20s} | {k_v3['n_win']-k_v4['n_win']:+d}W / {k_v3['n_loss']-k_v4['n_loss']:+d}L")
    print(f"{'Win Rate (%)':25s} | {k_v4['win_pct']:19.1f}% | {k_v3['win_pct']:19.1f}% | {k_v3['win_pct'] - k_v4['win_pct']:+5.1f}%")
    print(f"{'IC Wilson 95%':25s} | {k_v4['ci_95']:20s} | {k_v3['ci_95']:20s} | -")
    print(f"{'Payoff (AvgW / AvgL)':25s} | {k_v4['payoff']:20.2f} | {k_v3['payoff']:20.2f} | {k_v3['payoff'] - k_v4['payoff']:+5.2f}")
    print(f"{'Expectativa (R/op)':25s} | {k_v4['exp_r']:+19.4f}R | {k_v3['exp_r']:+19.4f}R | {k_v3['exp_r'] - k_v4['exp_r']:+7.4f}R")
    print(f"{'Net PnL (R)':25s} | {k_v4['net_r']:+19.2f}R | {k_v3['net_r']:+19.2f}R | {k_v3['net_r'] - k_v4['net_r']:+7.2f}R")
    print(f"{'Profit Factor (PF)':25s} | {k_v4['pf']:20.2f} | {k_v3['pf']:20.2f} | {k_v3['pf'] - k_v4['pf']:+5.2f}")
    print(f"{'Max Drawdown (R)':25s} | {k_v4['max_dd']:19.2f}R | {k_v3['max_dd']:19.2f}R | {k_v3['max_dd'] - k_v4['max_dd']:+5.2f}R")
    # Cálculo de los 3 niveles de fricción
    fric_low_v4 = eval_friction(t_v4['rr'], 0.025, 0.10)
    fric_low_v3 = eval_friction(t_v3['rr'], 0.025, 0.10)
    fric_mod_v4 = res_v4['k_mod']
    fric_mod_v3 = res_v3['k_mod']
    fric_sev_v4 = res_v4['k_sev']
    fric_sev_v3 = res_v3['k_sev']

    print(f"{'Fricción Baja Net R':25s} | {fric_low_v4['net_r']:+19.2f}R | {fric_low_v3['net_r']:+19.2f}R | {fric_low_v3['net_r'] - fric_low_v4['net_r']:+7.2f}R")
    print(f"{'Fricción Baja PF':25s} | {fric_low_v4['pf']:20.2f} | {fric_low_v3['pf']:20.2f} | {fric_low_v3['pf'] - fric_low_v4['pf']:+5.2f}")
    print(f"{'Fricción Moderada Net R':25s} | {fric_mod_v4['net_r']:+19.2f}R | {fric_mod_v3['net_r']:+19.2f}R | {fric_mod_v3['net_r'] - fric_mod_v4['net_r']:+7.2f}R")
    print(f"{'Fricción Moderada PF':25s} | {fric_mod_v4['pf']:20.2f} | {fric_mod_v3['pf']:20.2f} | {fric_mod_v3['pf'] - fric_mod_v4['pf']:+5.2f}")
    print(f"{'Fricción Severa Net R':25s} | {fric_sev_v4['net_r']:+19.2f}R | {fric_sev_v3['net_r']:+19.2f}R | {fric_sev_v3['net_r'] - fric_sev_v4['net_r']:+7.2f}R")
    print(f"{'Fricción Severa PF':25s} | {fric_sev_v4['pf']:20.2f} | {fric_sev_v3['pf']:20.2f} | {fric_sev_v3['pf'] - fric_sev_v4['pf']:+5.2f}")
    print(f"{'Holdout Puro (Fold 4)':25s} | {res_v4['k_holdout']['net_r']:+19.2f}R | {res_v3['k_holdout']['net_r']:+19.2f}R | {res_v3['k_holdout']['net_r'] - res_v4['k_holdout']['net_r']:+7.2f}R")

    # 2. Desglose de operaciones que cambian entre V4 y Var 3
    print("\n" + "=" * 125)
    print("2. ANÁLISIS FORENSE DE OPERACIONES ELIMINADAS O ALTERADAS:")
    print("=" * 125)
    merged = pd.merge(t_v4, t_v3[['time', 'symbol']], on=['time', 'symbol'], how='left', indicator=True)
    dropped = merged[merged['_merge'] == 'left_only'].copy()
    print(f"Operaciones de V4 ELIMINADAS en Var 3 (Total: {len(dropped)}):")
    for idx, row in dropped.iterrows():
        t_str = row['time'].strftime('%Y-%m-%d %H:%M')
        print(f"  * {t_str} | {row['symbol']:18s} | {row['direction']:4s} | ATR={row['risk_atr']:4.2f} | ADX={row['adx']:4.1f} | Outcome={row['outcome']:10s} | Realized={row['rr']:+6.2f}R")
    print(f"  --> PnL neto de las {len(dropped)} operaciones eliminadas: {dropped['rr'].sum():+.2f} R")
    print(f"  --> Desglose de eliminadas: {dict(dropped['outcome'].value_counts())}")

    # Chequear si Var 3 agregó operaciones que estaban bloqueadas en V4
    merged_inv = pd.merge(t_v3, t_v4[['time', 'symbol']], on=['time', 'symbol'], how='left', indicator=True)
    added = merged_inv[merged_inv['_merge'] == 'left_only'].copy()
    print(f"\nOperaciones NUEVAS aceptadas en Var 3 (liberadas por Cap=1) (Total: {len(added)}):")
    if len(added) > 0:
        for idx, row in added.iterrows():
            t_str = row['time'].strftime('%Y-%m-%d %H:%M')
            print(f"  * {t_str} | {row['symbol']:18s} | {row['direction']:4s} | ATR={row['risk_atr']:4.2f} | ADX={row['adx']:4.1f} | Outcome={row['outcome']:10s} | Realized={row['rr']:+6.2f}R")
        print(f"  --> PnL neto de las {len(added)} operaciones añadidas: {added['rr'].sum():+.2f} R")
    else:
        print("  * Ninguna operación adicional fue admitida (todas las de Var 3 son un subconjunto estricto de V4).")

    # 3. Desglose por Fold
    print("\n" + "=" * 125)
    print("3. DESGLOSE FOLD A FOLD (CONSISTENCIA TEMPORAL Y ESTABILIDAD):")
    print("=" * 125)
    print(f"{'Fold':7s} | {'V4 N':5s} | {'V4 WR':6s} | {'V4 NetR':8s} | {'V4 PF':6s} | {'Var3 N':6s} | {'Var3 WR':7s} | {'Var3 NetR':9s} | {'Var3 PF':7s} | {'Delta NetR':10s}")
    print("-" * 95)
    for i in range(4):
        f4 = res_v4['folds'][i]
        f3 = res_v3['folds'][i]
        delta = f3['net_r'] - f4['net_r']
        print(f"Fold {i+1:d}  | {f4['n']:5d} | {f4['win_pct']:5.1f}% | {f4['net_r']:+7.2f}R | {f4['pf']:6.2f} | {f3['n']:6d} | {f3['win_pct']:6.1f}% | {f3['net_r']:+8.2f}R | {f3['pf']:7.2f} | {delta:+9.2f}R")

    # 4. Desglose por Dirección (BUY vs SELL)
    print("\n" + "=" * 125)
    print("4. DESGLOSE POR DIRECCIÓN:")
    print("=" * 125)
    for d in ['BUY', 'SELL']:
        s4 = t_v4[t_v4['direction'] == d]
        s3 = t_v3[t_v3['direction'] == d]
        k4 = compute_detailed_kpis(s4['rr'], f"V4 {d}")
        k3 = compute_detailed_kpis(s3['rr'], f"Var3 {d}")
        print(f"Dirección {d:4s}:")
        print(f"  * V4:   N={k4['n']:2d} (W={k4['n_win']:2d}, L={k4['n_loss']:2d}) | WR: {k4['win_pct']:4.1f}% ({k4['ci_95']}) | Net R: {k4['net_r']:+6.2f}R | Exp: {k4['exp_r']:+6.4f}R | Payoff: {k4['payoff']:.2f} | PF: {k4['pf']:.2f} | MaxDD: {k4['max_dd']:.2f}R")
        print(f"  * Var3: N={k3['n']:2d} (W={k3['n_win']:2d}, L={k3['n_loss']:2d}) | WR: {k3['win_pct']:4.1f}% ({k3['ci_95']}) | Net R: {k3['net_r']:+6.2f}R | Exp: {k3['exp_r']:+6.4f}R | Payoff: {k3['payoff']:.2f} | PF: {k3['pf']:.2f} | MaxDD: {k3['max_dd']:.2f}R")

    # 5. Desglose por Activo (23 activos canónicos)
    print("\n" + "=" * 125)
    print("5. DESGLOSE POR ACTIVO EN LOS 23 SÍMBOLOS CANÓNICOS:")
    print("=" * 125)
    print(f"{'Símbolo':26s} | {'Subfamilia':10s} | {'V4 N':5s} | {'V4 WR':6s} | {'V4 NetR':8s} | {'Var3 N':6s} | {'Var3 WR':7s} | {'Var3 NetR':9s} | {'Efecto de ATR<=1.2'}")
    print("-" * 115)
    for sym in canonical_symbols:
        s4 = t_v4[t_v4['symbol'] == sym]
        s3 = t_v3[t_v3['symbol'] == sym]
        subfam = get_subfamily(sym)
        n4, n3 = len(s4), len(s3)
        pnl4 = s4['rr'].sum() if n4 > 0 else 0.0
        pnl3 = s3['rr'].sum() if n3 > 0 else 0.0
        wr4 = (len(s4[s4['rr']>0]) / n4 * 100) if n4 > 0 else 0.0
        wr3 = (len(s3[s3['rr']>0]) / n3 * 100) if n3 > 0 else 0.0

        if n4 == 0 and n3 == 0:
            effect = "Sin operaciones en ambas"
        elif n4 == n3 and pnl4 == pnl3:
            effect = "Idéntico (no afectado)"
        elif n3 < n4:
            effect = f"Eliminadas {n4 - n3} ops (Delta PnL: {pnl3 - pnl4:+.2f} R)"
        else:
            effect = f"Alterado (Delta PnL: {pnl3 - pnl4:+.2f} R)"

        print(f"{sym:26s} | {subfam:10s} | {n4:5d} | {wr4:5.1f}% | {pnl4:+7.2f}R | {n3:6d} | {wr3:6.1f}% | {pnl3:+8.2f}R | {effect}")

    # 6. Señales bloqueadas por Cap=1 en Var 3
    print("\n" + "=" * 125)
    print(f"6. SEÑALES BLOQUEADAS POR CAP=1 EN VARIANTE 3 ({len(res_v3['blocked'])} descartadas):")
    print("=" * 125)
    blk3 = res_v3['blocked']
    if len(blk3) > 0:
        for idx, row in blk3.iterrows():
            t_str = row['time'].strftime('%Y-%m-%d %H:%M')
            print(f"  * {t_str} | {row['symbol']:22s} | {row['direction']:4s} | Outcome: {row['outcome']:10s} | Realized: {row['rr']:+6.2f}R")
        print(f"  PnL Contrafactual Acumulado de Señales Bloqueadas: {blk3['rr'].sum():+.2f} R")

if __name__ == '__main__':
    main()
