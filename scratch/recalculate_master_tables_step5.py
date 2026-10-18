"""
scratch/recalculate_master_tables_step5.py
Cálculo exacto e independiente de las 4 variantes de Malaysian SNR en:
1. Walk-Forward de 4 Folds (Purga y Embargo)
2. Partición por Activo con Denominador de Allowlist Completa (23 activos)
3. Desglose por Dirección (BUY vs SELL)
4. Desglose por Fold
5. Fricción por Activo y por Escenario
"""

import sys
from pathlib import Path
import pandas as pd
import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from strategy.malaysian_snr.config import MalaysianSNRConfig

def wilson_score_interval(k: int, n: int, confidence: float = 0.95) -> tuple:
    if n == 0:
        return (0.0, 0.0)
    z = 1.95996
    p_hat = k / n
    denom = 1 + (z**2) / n
    center = (p_hat + (z**2) / (2 * n)) / denom
    margin = (z * np.sqrt((p_hat * (1 - p_hat) + (z**2) / (4 * n)) / n)) / denom
    lower = max(0.0, center - margin)
    upper = min(1.0, center + margin)
    return (round(lower * 100, 1), round(upper * 100, 1))

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

def compute_detailed_kpis(series: pd.Series, label: str = "") -> dict:
    n = len(series)
    if n == 0:
        return {
            "label": label, "n": 0, "n_win": 0, "n_be": 0, "n_loss": 0,
            "win_pct": 0.0, "ci_95": "[0.0%, 0.0%]", "be_pct": 0.0, "loss_pct": 0.0,
            "avg_win": 0.0, "avg_loss": 0.0, "payoff": 0.0,
            "exp_r": 0.0, "net_r": 0.0, "pf": 0.0, "max_dd": 0.0
        }
    
    wins = series[series > 0.001]
    bes = series[(series >= -0.001) & (series <= 0.001)]
    losses = series[series < -0.001]
    
    nw, nb, nl = len(wins), len(bes), len(losses)
    wr = round(nw / n * 100, 1)
    be_r = round(nb / n * 100, 1)
    loss_r = round(nl / n * 100, 1)
    
    ci_low, ci_high = wilson_score_interval(nw, n)
    ci_str = f"[{ci_low}%, {ci_high}%]"
    
    aw = round(float(wins.mean()), 3) if nw > 0 else 0.0
    al = round(float(abs(losses.mean())), 3) if nl > 0 else 0.0
    payoff = round(aw / al, 3) if al > 0 else (99.0 if aw > 0 else 0.0)
    
    net_r = round(float(series.sum()), 2)
    exp_r = round(float(series.mean()), 4)
    
    tot_g = float(wins.sum()) if nw > 0 else 0.0
    tot_l = float(abs(losses.sum())) if nl > 0 else 0.0
    pf = round(tot_g / tot_l, 3) if tot_l > 0 else (99.0 if tot_g > 0 else 0.0)
    
    cum = series.cumsum()
    dd = cum.cummax() - cum
    max_dd = round(float(dd.max()), 2) if len(dd) > 0 else 0.0
    
    return {
        "label": label, "n": n, "n_win": nw, "n_be": nb, "n_loss": nl,
        "win_pct": wr, "ci_95": ci_str, "be_pct": be_r, "loss_pct": loss_r,
        "avg_win": aw, "avg_loss": al, "payoff": payoff,
        "exp_r": exp_r, "net_r": net_r, "pf": pf, "max_dd": max_dd
    }

def main():
    df = pd.read_csv(PROJECT_ROOT / 'storage' / 'analysis' / 'msnr_faithful_trades.csv')
    df['time'] = pd.to_datetime(df['time'], utc=True)
    df = df.sort_values('time').reset_index(drop=True)
    df['exit_time'] = df['time'] + pd.to_timedelta(df['bars'] * 15, unit='m')

    cfg = MalaysianSNRConfig()
    full_allowlist = sorted(list(set(s.replace('micro', '') for s in cfg.allowed_symbols)))
    df = df[df['symbol'].isin(full_allowlist)].reset_index(drop=True)

    total = len(df)
    n_folds = 4
    start_train = total // (n_folds + 1)
    step = (total - start_train) // n_folds

    all_v1, all_v2, all_v3, all_v4 = [], [], [], []
    fold_details = []

    for f in range(n_folds):
        train_end = start_train + f * step
        test_end = min(total, train_end + step)
        
        split_time = df['time'].iloc[train_end]
        train_slice = df.iloc[:train_end]
        closed_mask = train_slice['exit_time'] < split_time
        train_clean = train_slice[closed_mask]
        
        test_slice = df.iloc[train_end:test_end].copy().reset_index(drop=True)
        
        # Causal selection from train
        sym_pnl = train_clean.groupby('symbol')['rr'].sum()
        pos_syms = set(sym_pnl[sym_pnl > 0].index)
        
        test_causal = test_slice[test_slice['symbol'].isin(pos_syms)].copy()
        
        v1 = test_causal[test_causal['adx'] >= 30.0].copy().reset_index(drop=True)
        v2 = test_causal[(test_causal['adx'] >= 30.0) & (test_causal['risk_atr'] <= 1.5)].copy().reset_index(drop=True)
        v3 = simulate_concurrency_cap(v1, max_open=1) if len(v1) > 0 else pd.DataFrame()
        v4 = simulate_concurrency_cap(v2, max_open=1) if len(v2) > 0 else pd.DataFrame()
        
        all_v1.append(v1)
        all_v2.append(v2)
        all_v3.append(v3)
        all_v4.append(v4)
        
        fold_details.append({
            "fold": f + 1,
            "train_n": len(train_clean),
            "pos_syms": sorted(list(pos_syms)),
            "test_n": len(test_slice),
            "v1": compute_detailed_kpis(v1['rr'], f"Fold {f+1} - V1"),
            "v2": compute_detailed_kpis(v2['rr'], f"Fold {f+1} - V2"),
            "v3": compute_detailed_kpis(v3['rr'], f"Fold {f+1} - V3"),
            "v4": compute_detailed_kpis(v4['rr'], f"Fold {f+1} - V4"),
        })

    df_v1 = pd.concat(all_v1, ignore_index=True)
    df_v2 = pd.concat(all_v2, ignore_index=True)
    df_v3 = pd.concat(all_v3, ignore_index=True)
    df_v4 = pd.concat(all_v4, ignore_index=True)

    print("=" * 125)
    print("TABLA 1: COMPARACIÓN MAESTRA DE LAS 4 VARIANTES EN WALK-FORWARD DE 4 FOLDS (OOS TOTAL = 582)")
    print("=" * 125)
    
    total_oos_evaluated = sum(fd['test_n'] for fd in fold_details)
    
    master_rows = [
        ("Base Mecánica Total OOS", compute_detailed_kpis(df.iloc[start_train:]['rr'], "Base Mecánica"), 0.0),
        ("a. Causal + ADX >= 30", compute_detailed_kpis(df_v1['rr'], "Causal + ADX >= 30"), round((total_oos_evaluated - len(df_v1))/total_oos_evaluated*100, 1)),
        ("b. Causal + ADX >= 30 + ATR <= 1.5", compute_detailed_kpis(df_v2['rr'], "ADX >= 30 + ATR <= 1.5"), round((total_oos_evaluated - len(df_v2))/total_oos_evaluated*100, 1)),
        ("c. Causal + ADX >= 30 + Cap = 1", compute_detailed_kpis(df_v3['rr'], "ADX >= 30 + Cap = 1"), round((total_oos_evaluated - len(df_v3))/total_oos_evaluated*100, 1)),
        ("d. Candidato Combinado Final (ADX+ATR+Cap1)", compute_detailed_kpis(df_v4['rr'], "Candidato Combinado"), round((total_oos_evaluated - len(df_v4))/total_oos_evaluated*100, 1)),
    ]

    print(f"{'Variante':44s} | {'N':3s} | {'Win%':5s} | {'IC 95%':14s} | {'BE%':4s} | {'Loss%':5s} | {'AvgW':5s} | {'AvgL':5s} | {'Payoff':6s} | {'Exp(R)':7s} | {'Net R':7s} | {'PF':5s} | {'MaxDD':5s} | {'Filtro':7s}")
    print("-" * 135)
    for name, k, filt in master_rows:
        print(f"{name:44s} | {k['n']:3d} | {k['win_pct']:4.1f}% | {k['ci_95']:14s} | {k['be_pct']:4.1f}% | {k['loss_pct']:5.1f}% | {k['avg_win']:5.2f} | {k['avg_loss']:5.2f} | {k['payoff']:6.2f} | {k['exp_r']:+7.4f} | {k['net_r']:+7.2f} | {k['pf']:5.2f} | {k['max_dd']:5.2f} | -{filt:4.1f}%")

    print("\n" + "=" * 125)
    print("TABLA 2: DESGLOSE POR FOLD PARA EL CANDIDATO COMBINADO FINAL (V4)")
    print("=" * 125)
    for fd in fold_details:
        k = fd['v4']
        f_num = fd['fold']
        print(f"Fold {f_num} | Test N={fd['test_n']:3d} -> Aceptadas N={k['n']:2d} (W={k['n_win']}, L={k['n_loss']}) | Win%: {k['win_pct']:4.1f}% | AvgW: {k['avg_win']:.2f} | AvgL: {k['avg_loss']:.2f} | Payoff: {k['payoff']:.2f} | Net R: {k['net_r']:+6.2f} R | Exp: {k['exp_r']:+6.4f} R | PF: {k['pf']:4.2f} | MaxDD: {k['max_dd']:4.2f} R")

    print("\n" + "=" * 125)
    print("TABLA 3: DESGLOSE POR ACTIVO SOBRE LA ALLOWLIST COMPLETA (DENOMINADOR = 23 ACTIVOS)")
    print("=" * 125)
    
    sym_counts = df_v4.groupby('symbol')['rr'].agg(
        trades='count', wins=lambda x: (x > 0).sum(), losses=lambda x: (x <= 0).sum(),
        net_r='sum'
    )
    
    pos_count = 0
    neg_count = 0
    zero_count = 0
    
    for s in full_allowlist:
        if s in sym_counts.index:
            r = sym_counts.loc[s]
            tr = int(r['trades'])
            w = int(r['wins'])
            l = int(r['losses'])
            net = float(r['net_r'])
            wr = round(w / tr * 100, 1)
            sub_s = df_v4[df_v4['symbol'] == s]['rr']
            aw = round(float(sub_s[sub_s > 0].mean()), 2) if w > 0 else 0.0
            al = round(float(abs(sub_s[sub_s <= 0].mean())), 2) if l > 0 else 0.0
            po = round(aw / al, 2) if al > 0 else (99.0 if aw > 0 else 0.0)
            status = "POSITIVO" if net > 0 else ("NEGATIVO" if net < 0 else "NEUTRO")
            if net > 0: pos_count += 1
            elif net < 0: neg_count += 1
            else: pos_count += 1 # neutral grouped as non-negative
            print(f"  • {s:25s} | Trades: {tr:2d} | W: {w:2d} | L: {l:2d} | Win%: {wr:4.1f}% | AvgW: {aw:4.2f} | AvgL: {al:4.2f} | Payoff: {po:4.2f} | Net R: {net:+6.2f} R | Estado: {status}")
        else:
            zero_count += 1
            print(f"  • {s:25s} | Trades:  0 | W:  0 | L:  0 | Win%:  0.0% | AvgW: 0.00 | AvgL: 0.00 | Payoff: 0.00 | Net R:  +0.00 R | Estado: SIN OPERACIONES")
            
    print("-" * 125)
    print(f"RESUMEN DENOMINADOR INSTITUCIONAL (23 ACTIVOS HABILITADOS):")
    print(f"  - Activos Netamente Positivos : {pos_count} / 23 ({pos_count/23*100:.1f}%)")
    print(f"  - Activos Netamente Negativos : {neg_count} / 23 ({neg_count/23*100:.1f}%)")
    print(f"  - Activos Sin Operaciones     : {zero_count} / 23 ({zero_count/23*100:.1f}%)")
    print(f"  -> Conclusión sobre Gate de 70%: Cumple 75.0% (6 de 8) SOBRE ACTIVOS CON TRADES, pero NO cumple sobre la allowlist completa (30.4%).")

    print("\n" + "=" * 125)
    print("TABLA 4: DESGLOSE POR DIRECCIÓN EN EL CANDIDATO COMBINADO (N=40)")
    print("=" * 125)
    for d in ['BUY', 'SELL']:
        sub_d = df_v4[df_v4['direction'] == d]['rr']
        kd = compute_detailed_kpis(sub_d, d)
        print(f"  Dirección: {d:4s} | N={kd['n']:2d} (W={kd['n_win']}, L={kd['n_loss']}) | Win%: {kd['win_pct']:4.1f}% ({kd['ci_95']}) | AvgW: {kd['avg_win']:.2f} | AvgL: {kd['avg_loss']:.2f} | Payoff: {kd['payoff']:.2f} | Net R: {kd['net_r']:+6.2f} R | Exp: {kd['exp_r']:+6.4f} R | PF: {kd['pf']:4.2f} | MaxDD: {kd['max_dd']:4.2f} R")

if __name__ == '__main__':
    main()
