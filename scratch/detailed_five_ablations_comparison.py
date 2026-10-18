"""
scratch/detailed_five_ablations_comparison.py
Comparación pareada completa y detallada de las 5 variantes solicitadas:
1. Benchmark V4 (ADX>=30, ATR<=1.5, Cap=1)
2. ATR <= 1.2 solo en Metales
3. ATR <= 1.2 solo en Forex
4. ATR <= 1.2 en Metales y Forex
5. Variante ATR + Body Ratio >= 0.50 en Sintéticos
"""

import sys
from pathlib import Path
import pandas as pd
import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from strategy.malaysian_snr.config import MalaysianSNRConfig
from scratch.test_subfamily_and_filter_improvements import (
    evaluate_variant, get_subfamily, wilson_score_interval, compute_detailed_kpis, eval_friction
)

def main():
    csv_path = PROJECT_ROOT / "scratch" / "msnr_complete_23_faithful_trades_clean.csv"
    df = pd.read_csv(csv_path)
    df['time'] = pd.to_datetime(df['time'], utc=True)
    df['exit_time'] = pd.to_datetime(df['exit_time'], utc=True)
    df['subfamily'] = df['symbol'].apply(get_subfamily)
    df = df.sort_values('time').reset_index(drop=True)

    # Definición de las 5 variantes
    def f_v4(d):
        return d[(d['adx'] >= 30.0) & (d['risk_atr'] <= 1.5)]

    def f_metals_only(d):
        c_m = (d['subfamily'] == 'METALS') & (d['adx'] >= 30.0) & (d['risk_atr'] <= 1.2)
        c_o = (d['subfamily'] != 'METALS') & (d['adx'] >= 30.0) & (d['risk_atr'] <= 1.5)
        return d[c_m | c_o]

    def f_forex_only(d):
        c_f = (d['subfamily'] == 'FOREX') & (d['adx'] >= 30.0) & (d['risk_atr'] <= 1.2)
        c_o = (d['subfamily'] != 'FOREX') & (d['adx'] >= 30.0) & (d['risk_atr'] <= 1.5)
        return d[c_f | c_o]

    def f_metals_forex(d):
        c_mf = (d['subfamily'].isin(['FOREX', 'METALS'])) & (d['adx'] >= 30.0) & (d['risk_atr'] <= 1.2)
        c_s = (d['subfamily'] == 'SYNTH') & (d['adx'] >= 30.0) & (d['risk_atr'] <= 1.5)
        return d[c_mf | c_s]

    def f_comb_body50(d):
        c_mf = (d['subfamily'].isin(['FOREX', 'METALS'])) & (d['adx'] >= 30.0) & (d['risk_atr'] <= 1.2)
        c_s = (d['subfamily'] == 'SYNTH') & (d['adx'] >= 30.0) & (d['risk_atr'] <= 1.5) & (d['body_ratio'] >= 0.50)
        return d[c_mf | c_s]

    variants = [
        ("1. Benchmark V4", f_v4),
        ("2. ATR <= 1.2 Solo Metales", f_metals_only),
        ("3. ATR <= 1.2 Solo Forex", f_forex_only),
        ("4. ATR <= 1.2 Metales + Forex", f_metals_forex),
        ("5. Var ATR + Sint. Body>=0.50", f_comb_body50),
    ]

    results = {}
    for name, f_func in variants:
        res = evaluate_variant(df, f_func, cap=1, n_folds=4)
        results[name] = res

    # 1. Tabla Resumen Global
    print("=" * 140)
    print("RESUMEN GLOBAL COMPARATIVO (5 VARIANTES, 23 ACTIVOS CANÓNICOS)")
    print("=" * 140)
    print(f"{'Variante':32s} | {'N':2s} | {'Win%':5s} | {'IC Wilson 95%':16s} | {'Payoff':6s} | {'Exp (R)':8s} | {'Net R':8s} | {'PF':5s} | {'MaxDD':6s} | {'Fric.Baja':9s} | {'Fric.Mod':8s} | {'Fric.Sev':8s}")
    print("-" * 140)
    for name, res in results.items():
        k = res['k_tot']
        tdf = res['trades']
        f_low = eval_friction(tdf['rr'], 0.025, 0.10)
        f_mod = res['k_mod']
        f_sev = res['k_sev']
        print(f"{name:32s} | {k['n']:2d} | {k['win_pct']:4.1f}% | {k['ci_95']:16s} | {k['payoff']:6.2f} | {k['exp_r']:+7.4f}R | {k['net_r']:+7.2f}R | {k['pf']:5.2f} | {k['max_dd']:5.2f}R | {f_low['net_r']:+8.2f}R | {f_mod['net_r']:+7.2f}R | {f_sev['net_r']:+7.2f}R")

    # 2. Desglose Fold a Fold
    print("\n" + "=" * 140)
    print("ESTABILIDAD TEMPORAL POR FOLD (WALK-FORWARD CRONOLÓGICO)")
    print("=" * 140)
    for name, res in results.items():
        print(f"\n--- {name} ---")
        for i, fk in enumerate(res['folds']):
            label = f"Fold {i+1}" + (" (Holdout Intacto)" if i == 3 else "")
            print(f"  {label:25s}: N={fk['n']:2d} | W={fk['n_win']:2d}, L={fk['n_loss']:2d} | Win%: {fk['win_pct']:4.1f}% | Net: {fk['net_r']:+6.2f}R | Exp: {fk['exp_r']:+6.4f}R | PF: {fk['pf']:4.2f} | MaxDD: {fk['max_dd']:4.2f}R")

    # 3. Autopsia de Operaciones Excluidas vs V4
    v4_trades = results["1. Benchmark V4"]['trades'].copy()
    v4_trades['key'] = v4_trades['time'].astype(str) + "_" + v4_trades['symbol']

    print("\n" + "=" * 140)
    print("AUTOPSIA FORENSE DE OPERACIONES EXCLUIDAS RESPECTO A BENCHMARK V4")
    print("=" * 140)
    for name in ["2. ATR <= 1.2 Solo Metales", "3. ATR <= 1.2 Solo Forex", "4. ATR <= 1.2 Metales + Forex", "5. Var ATR + Sint. Body>=0.50"]:
        var_trades = results[name]['trades'].copy()
        var_keys = set(var_trades['time'].astype(str) + "_" + var_trades['symbol'])
        excluded = v4_trades[~v4_trades['key'].isin(var_keys)]
        print(f"\n--- Exclusiones en {name} (Total: {len(excluded)} ops) ---")
        ev_loss = 0.0
        om_win = 0.0
        for idx, row in excluded.iterrows():
            diag = "Pérdida Evitada" if row['rr'] < 0 else "Ganancia Omitida"
            if row['rr'] < 0:
                ev_loss += abs(row['rr'])
            else:
                om_win += row['rr']
            print(f"  {str(row['time'])[:16]} | {row['symbol']:18s} | {row['direction']:4s} | ATR={row['risk_atr']:.2f} | ADX={row['adx']:.1f} | Body={row['body_ratio']:.2f} | RR={row['rr']:+5.2f}R | {diag}")
        net_impact = ev_loss - om_win
        print(f"  Balance neto de exclusión: +{ev_loss:.2f}R pérdidas evitadas - {om_win:.2f}R ganancias omitidas = {net_impact:+.2f}R impacto neto en PnL")

    # 4. Desglose por Dirección (BUY vs SELL)
    print("\n" + "=" * 140)
    print("DESGLOSE POR DIRECCIÓN (BUY vs SELL)")
    print("=" * 140)
    for name, res in results.items():
        tdf = res['trades']
        b_df = tdf[tdf['direction'] == 'BUY']
        s_df = tdf[tdf['direction'] == 'SELL']
        kb = compute_detailed_kpis(b_df['rr'])
        ks = compute_detailed_kpis(s_df['rr'])
        print(f"{name:32s} | BUY:  N={kb['n']:2d}, WR={kb['win_pct']:4.1f}% ({kb['ci_95']:16s}), Net={kb['net_r']:+6.2f}R, PF={kb['pf']:4.2f}, MaxDD={kb['max_dd']:4.2f}R")
        print(f"{'':32s} | SELL: N={ks['n']:2d}, WR={ks['win_pct']:4.1f}% ({ks['ci_95']:16s}), Net={ks['net_r']:+6.2f}R, PF={ks['pf']:4.2f}, MaxDD={ks['max_dd']:4.2f}R")

    # 5. Cobertura Institucional de Activos (Denominador = 23)
    print("\n" + "=" * 140)
    print("COBERTURA INSTITUCIONAL DE ACTIVOS (DENOMINADOR = 23 SÍMBOLOS CANÓNICOS)")
    print("=" * 140)
    cfg = MalaysianSNRConfig()
    canonical = sorted(list(set(s.replace('micro', '') for s in cfg.allowed_symbols)))
    for name, res in results.items():
        tdf = res['trades']
        pnl_s = tdf.groupby('symbol')['rr'].sum()
        pos = [s for s in canonical if pnl_s.get(s, 0) > 0]
        neg = [s for s in canonical if pnl_s.get(s, 0) < 0]
        zero = [s for s in canonical if pnl_s.get(s, 0) == 0]
        print(f"{name:32s} | Positivos: {len(pos):2d} / 23 ({len(pos)/23*100:4.1f}%) | Negativos: {len(neg):2d} ({len(neg)/23*100:4.1f}%) | Sin Trades: {len(zero):2d} ({len(zero)/23*100:4.1f}%)")

if __name__ == '__main__':
    main()
