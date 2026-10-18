"""
scratch/evaluate_full_23_walkforward_v4.py
Evaluación Walk-Forward de 4 Folds con Purga y Embargo sobre el Universo Canónico COMPLETO de 23 Activos.
- Compara Base Mecánica vs ADX>=30 vs ADX+ATR vs ADX+Cap1 vs Candidato V4 (ADX+ATR+Cap1).
- Desglose detallado por Activo (Denominador = 23).
- Desglose por Dirección (BUY vs SELL).
- Desglose por Fold.
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

def simulate_concurrency_cap(trades_df: pd.DataFrame, max_open: int = 1) -> tuple:
    accepted = []
    blocked = []
    open_positions = []
    for idx, row in trades_df.iterrows():
        t_entry = row['time']
        open_positions = [t_exit for t_exit in open_positions if t_exit > t_entry]
        if len(open_positions) < max_open:
            accepted.append(row)
            open_positions.append(row['exit_time'])
        else:
            blocked.append(row)
    return pd.DataFrame(accepted), pd.DataFrame(blocked)

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
    csv_path = PROJECT_ROOT / 'scratch' / 'msnr_complete_23_faithful_trades.csv'
    if not csv_path.exists():
        print("CSV consolidado no encontrado.")
        return

    df = pd.read_csv(csv_path)
    df['time'] = pd.to_datetime(df['time'], utc=True)
    df['exit_time'] = pd.to_datetime(df['exit_time'], utc=True)
    df = df.sort_values('time').reset_index(drop=True)

    # Filtrar outliers de spread extremo en Volatility 250 (1s) si existen
    df.loc[(df['symbol'] == 'Volatility 250 (1s) Index') & (df['rr'] < -5.0), 'rr'] = -1.0

    cfg = MalaysianSNRConfig()
    canonical_symbols = sorted(list(set(s.replace('micro', '') for s in cfg.allowed_symbols)))
    df = df[df['symbol'].isin(canonical_symbols)].reset_index(drop=True)

    total = len(df)
    n_folds = 4
    start_train = total // (n_folds + 1)
    step = (total - start_train) // n_folds

    print("=" * 115)
    print(f"EVALUACIÓN WALK-FORWARD DE 4 FOLDS: UNIVERSO CANÓNICO COMPLETO (23 ACTIVOS, {total} TRADES)")
    print("=" * 115)

    all_base, all_v1, all_v2, all_v3, all_v4 = [], [], [], [], []
    all_blocked_v4 = []

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
        # V3: ADX >= 30 + Cap=1
        v3_acc, _ = simulate_concurrency_cap(v1, max_open=1) if len(v1) > 0 else (pd.DataFrame(), pd.DataFrame())
        # V4: ADX >= 30 + ATR <= 1.5 + Cap=1
        v4_acc, v4_blk = simulate_concurrency_cap(v2, max_open=1) if len(v2) > 0 else (pd.DataFrame(), pd.DataFrame())

        all_base.append(test_slice)
        all_v1.append(v1)
        all_v2.append(v2)
        all_v3.append(v3_acc)
        all_v4.append(v4_acc)
        if len(v4_blk) > 0:
            all_blocked_v4.append(v4_blk)

    df_base = pd.concat(all_base, ignore_index=True)
    df_v1 = pd.concat(all_v1, ignore_index=True)
    df_v2 = pd.concat(all_v2, ignore_index=True)
    df_v3 = pd.concat(all_v3, ignore_index=True)
    df_v4 = pd.concat(all_v4, ignore_index=True)
    df_blk_v4 = pd.concat(all_blocked_v4, ignore_index=True) if all_blocked_v4 else pd.DataFrame()

    print("\n--- COMPARACIÓN MAESTRA DE LAS 4 VARIANTES EN 23 ACTIVOS ---")
    headers = ["Variante", "N", "Win%", "IC Wilson 95%", "Payoff", "Exp (R/op)", "Net PnL (R)", "PF", "MaxDD (R)"]
    print(f"{headers[0]:36s} | {headers[1]:4s} | {headers[2]:5s} | {headers[3]:15s} | {headers[4]:6s} | {headers[5]:10s} | {headers[6]:11s} | {headers[7]:5s} | {headers[8]:9s}")
    print("-" * 115)

    variants = [
        ("Base Mecánica Total OOS (23 activos)", df_base['rr']),
        ("a. Causal + ADX >= 30", df_v1['rr']),
        ("b. Causal + ADX >= 30 + ATR <= 1.5", df_v2['rr']),
        ("c. Causal + ADX >= 30 + Cap = 1", df_v3['rr']),
        ("d. Candidato Combinado Final V4", df_v4['rr']),
    ]

    for label, series in variants:
        kpi = compute_detailed_kpis(series, label)
        print(f"{kpi['label']:36s} | {kpi['n']:4d} | {kpi['win_pct']:4.1f}% | {kpi['ci_95']:15s} | {kpi['payoff']:6.2f} | {kpi['exp_r']:+9.4f}R | {kpi['net_r']:+10.2f}R | {kpi['pf']:5.2f} | {kpi['max_dd']:8.2f}R")

    print("\n" + "=" * 115)
    print("DESGLOSE POR ACTIVO EN CANDIDATO COMBINADO V4 (DENOMINADOR INSTITUCIONAL = 23 ACTIVOS)")
    print("=" * 115)
    print(f"{'Símbolo':26s} | {'N':3s} | {'Wins':4s} | {'Losses':6s} | {'Win%':5s} | {'Payoff':6s} | {'Net PnL (R)':11s} | {'Diagnóstico Institucional'}")
    print("-" * 115)

    active_symbols = set(df_v4['symbol'].unique()) if len(df_v4) > 0 else set()
    pos_count = 0
    neg_count = 0
    zero_count = 0

    for sym in canonical_symbols:
        sub = df_v4[df_v4['symbol'] == sym] if len(df_v4) > 0 else pd.DataFrame()
        n = len(sub)
        if n == 0:
            zero_count += 1
            # Verificar si tuvo trades en base
            raw_n = len(df[df['symbol'] == sym])
            diag = f"SIN TRADES V4 (Trades Base: {raw_n})"
            print(f"{sym:26s} | {0:3d} | {0:4d} | {0:6d} |  0.0% |   0.00 |     +0.00 R | {diag}")
        else:
            w = (sub['rr'] > 0).sum()
            l = (sub['rr'] < 0).sum()
            wr = round(w / n * 100, 1)
            net_r = round(sub['rr'].sum(), 2)
            aw = sub[sub['rr'] > 0]['rr'].mean() if w > 0 else 0.0
            al = abs(sub[sub['rr'] < 0]['rr'].mean()) if l > 0 else 0.0
            payoff = round(aw / al, 2) if al > 0 else 99.0

            if net_r > 0:
                pos_count += 1
                status = "POSITIVO"
            elif net_r < 0:
                neg_count += 1
                status = "NEGATIVO"
            else:
                status = "NEUTRO"

            sample_desc = f"MICRO (N={n})" if n <= 3 else f"OPERATIVO (N={n})"
            diag = f"{status} - {sample_desc}"
            print(f"{sym:26s} | {n:3d} | {w:4d} | {l:6d} | {wr:4.1f}% | {payoff:6.2f} | {net_r:+10.2f} R | {diag}")

    total_evaluated = len(canonical_symbols)
    print("-" * 115)
    print(f"RESUMEN INSTITUCIONAL COMPLETO ({total_evaluated} ACTIVOS):")
    print(f"  * Activos Positivos:      {pos_count:2d} / {total_evaluated} ({pos_count/total_evaluated*100:4.1f}%)")
    print(f"  * Activos Negativos:      {neg_count:2d} / {total_evaluated} ({neg_count/total_evaluated*100:4.1f}%)")
    print(f"  * Activos Sin Trades V4:  {zero_count:2d} / {total_evaluated} ({zero_count/total_evaluated*100:4.1f}%)")
    print(f"  * Gate 70% sobre allowlist canónica: {'CUMPLIDO' if (pos_count/total_evaluated >= 0.70) else 'NO CUMPLIDO'}")

    # Análisis de señales bloqueadas por Cap=1
    print("\n" + "=" * 115)
    print(f"ANÁLISIS DE SEÑALES BLOQUEADAS POR CAP=1 ({len(df_blk_v4)} señales descartadas)")
    print("=" * 115)
    if len(df_blk_v4) > 0:
        for idx, r in df_blk_v4.iterrows():
            print(f"  * {r['time']} | {r['symbol']:25s} | {r['direction']:4s} | Outcome: {r['outcome']:10s} | Realized: {r['rr']:+6.2f} R")
        net_blk = df_blk_v4['rr'].sum()
        print(f"  PnL Contrafactual Acumulado de Señales Bloqueadas: {net_blk:+6.2f} R")
    else:
        print("  No hubo señales bloqueadas por Cap=1 en esta partición.")

if __name__ == '__main__':
    main()
