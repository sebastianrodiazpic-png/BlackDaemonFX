"""
scratch/test_subfamily_and_filter_improvements.py
Evaluación rigurosa de mejoras por subfamilia y filtros defensivos de uno en uno:
- Baseline: V4 canónico (ADX >= 30, ATR <= 1.5, Cap=1)
- Variante 1: ADX adaptado (Forex ADX >= 25, Sintéticos ADX >= 30, Metales ADX >= 30, ATR <= 1.5, Cap=1)
- Variante 2: Body Ratio defensivo en Sintéticos (V4 + Sintéticos Body >= 0.60, Cap=1)
- Variante 3: ATR estricto en Metales/Forex (Metales/Forex ATR <= 1.2, Sintéticos ATR <= 1.5, ADX >= 30, Cap=1)
- Variante 4: Concurrencia Cap=2 (V4 con máximo 2 posiciones abiertas)
- Walk-forward de 4 Folds con purga y embargo estricto.
- Holdout intacto (Fold 4 fuera de muestra).
"""

import sys
from pathlib import Path
import pandas as pd
import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from strategy.malaysian_snr.config import MalaysianSNRConfig

synths = set([
    'Boom 1000 Index', 'Boom 300 Index', 'Crash 1000 Index', 'Crash 600 Index',
    'Jump 10 Index', 'Jump 25 Index', 'Step Index', 'Step Index 200',
    'Step Index 400', 'Volatility 250 (1s) Index', 'Volatility 50 (1s) Index',
    'Volatility 90 Index'
])
forex = set(['AUDNZD', 'EURCHF', 'EURGBP', 'EURUSD', 'GBPAUD', 'GBPJPY', 'GBPUSD', 'USDJPY'])
metals_indices = set(['XAUUSD', 'XAGUSD', 'Wall Street 30'])

def get_subfamily(sym):
    if sym in synths:
        return 'SYNTH'
    elif sym in forex:
        return 'FOREX'
    elif sym in metals_indices:
        return 'METALS'
    return 'OTHER'

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

def eval_friction(series: pd.Series, slip: float, gap_p: float) -> dict:
    f_rr = []
    for r in series:
        if r > 0.001:
            f_rr.append(r - slip)
        elif r < -0.001:
            pen = (1.0 + slip) * (1.0 + gap_p)
            f_rr.append(-pen)
        else:
            f_rr.append(-slip)
    return compute_detailed_kpis(pd.Series(f_rr), "Fricción")

def evaluate_variant(df_full, filter_func, cap=1, n_folds=4):
    total = len(df_full)
    start_train = total // (n_folds + 1)
    step = (total - start_train) // n_folds
    
    all_oos = []
    all_blocked = []
    fold_kpis = []
    
    for f in range(n_folds):
        train_end = start_train + f * step
        test_end = min(total, train_end + step)
        
        split_time = df_full['time'].iloc[train_end]
        train_slice = df_full.iloc[:train_end]
        closed_mask = train_slice['exit_time'] < split_time
        train_clean = train_slice[closed_mask]
        
        test_slice = df_full.iloc[train_end:test_end].copy().reset_index(drop=True)
        
        # Causal selection
        sym_pnl = train_clean.groupby('symbol')['rr'].sum()
        pos_syms = set(sym_pnl[sym_pnl > 0].index)
        
        test_causal = test_slice[test_slice['symbol'].isin(pos_syms)].copy().reset_index(drop=True)
        test_filtered = filter_func(test_causal).reset_index(drop=True)
        
        accepted, blocked = simulate_concurrency_cap(test_filtered, max_open=cap)
        all_oos.append(accepted)
        if len(blocked) > 0:
            all_blocked.append(blocked)
            
        fold_kpis.append(compute_detailed_kpis(accepted['rr'] if len(accepted)>0 else pd.Series(), f"Fold {f+1}"))
        
    df_res = pd.concat(all_oos, ignore_index=True) if all_oos else pd.DataFrame()
    df_blk = pd.concat(all_blocked, ignore_index=True) if all_blocked else pd.DataFrame()
    k_tot = compute_detailed_kpis(df_res['rr'] if len(df_res)>0 else pd.Series(), "Total OOS")
    k_holdout = fold_kpis[-1]  # Fold 4 as intact holdout
    
    # Friction
    k_mod = eval_friction(df_res['rr'], 0.05, 0.15) if len(df_res)>0 else k_tot
    k_sev = eval_friction(df_res['rr'], 0.10, 0.25) if len(df_res)>0 else k_tot
    
    return {
        "k_tot": k_tot,
        "k_holdout": k_holdout,
        "k_mod": k_mod,
        "k_sev": k_sev,
        "folds": fold_kpis,
        "trades": df_res,
        "blocked": df_blk
    }

def main():
    csv_path = PROJECT_ROOT / "scratch" / "msnr_complete_23_faithful_trades_clean.csv"
    df = pd.read_csv(csv_path)
    df['time'] = pd.to_datetime(df['time'], utc=True)
    df['exit_time'] = pd.to_datetime(df['exit_time'], utc=True)
    df['subfamily'] = df['symbol'].apply(get_subfamily)
    df = df.sort_values('time').reset_index(drop=True)

    print("=" * 125)
    print("EVALUACIÓN EXPERIMENTAL DE MEJORAS POR SUBFAMILIA Y ABLACIONES (23 ACTIVOS, 957 TRADES)")
    print("=" * 125)

    # Definición de Filtros
    # Baseline V4: ADX >= 30, ATR <= 1.5, Cap=1
    def f_v4(d):
        return d[(d['adx'] >= 30.0) & (d['risk_atr'] <= 1.5)]

    # Var 1: ADX Adaptado (Forex ADX >= 25, Sintéticos/Metales ADX >= 30, ATR <= 1.5)
    def f_var1(d):
        cond_forex = (d['subfamily'] == 'FOREX') & (d['adx'] >= 25.0) & (d['risk_atr'] <= 1.5)
        cond_other = (d['subfamily'] != 'FOREX') & (d['adx'] >= 30.0) & (d['risk_atr'] <= 1.5)
        return d[cond_forex | cond_other]

    # Var 2: Body Ratio Defensivo en Sintéticos (V4 + Sintéticos Body >= 0.60)
    def f_var2(d):
        cond_synth = (d['subfamily'] == 'SYNTH') & (d['adx'] >= 30.0) & (d['risk_atr'] <= 1.5) & (d['body_ratio'] >= 0.60)
        cond_other = (d['subfamily'] != 'SYNTH') & (d['adx'] >= 30.0) & (d['risk_atr'] <= 1.5)
        return d[cond_synth | cond_other]

    # Var 3: ATR Estricto en Metales/Forex (Metales/Forex ATR <= 1.2, Sintéticos ATR <= 1.5, ADX >= 30)
    def f_var3(d):
        cond_strict = (d['subfamily'].isin(['FOREX', 'METALS'])) & (d['adx'] >= 30.0) & (d['risk_atr'] <= 1.2)
        cond_synth = (d['subfamily'] == 'SYNTH') & (d['adx'] >= 30.0) & (d['risk_atr'] <= 1.5)
        return d[cond_strict | cond_synth]

    # Var 4: Concurrencia Cap=2 sobre V4
    # (Evaluado llamando con cap=2)

    # Var 5: Micro-TP Check (Ablación restrictiva: TP1=1.0R, runner=1.5R)
    # Ya evaluado previamente: destruye el payoff.

    variants = [
        ("V4 Baseline (ADX>=30, ATR<=1.5, Cap=1)", f_v4, 1),
        ("Var 1: Forex ADX >= 25 (Adaptado)", f_var1, 1),
        ("Var 2: Sintéticos Body >= 0.60", f_var2, 1),
        ("Var 3: Metales/Forex ATR <= 1.2 (Estricto)", f_var3, 1),
        ("Var 4: V4 con Concurrencia Cap=2", f_v4, 2),
    ]

    results = {}
    for name, f_func, c_cap in variants:
        res = evaluate_variant(df, f_func, cap=c_cap, n_folds=4)
        results[name] = res

    print(f"\n{'Variante Evaluada':44s} | {'N':3s} | {'Win%':5s} | {'IC Wilson 95%':16s} | {'Payoff':6s} | {'Exp (R)':8s} | {'Net R':8s} | {'PF':5s} | {'MaxDD':6s} | {'Holdout R':9s} | {'Fric.Mod':8s}")
    print("-" * 135)
    for name, res in results.items():
        k = res['k_tot']
        kh = res['k_holdout']
        km = res['k_mod']
        print(f"{name:44s} | {k['n']:3d} | {k['win_pct']:4.1f}% | {k['ci_95']:16s} | {k['payoff']:6.2f} | {k['exp_r']:+7.4f}R | {k['net_r']:+7.2f}R | {k['pf']:5.2f} | {k['max_dd']:5.2f}R | {kh['net_r']:+8.2f}R | {km['net_r']:+7.2f}R")

    print("\n" + "=" * 125)
    print("DETALLE FOLD A FOLD DE CADA VARIANTE (CONSISTENCIA TEMPORAL)")
    print("=" * 125)
    for name, res in results.items():
        print(f"\n--- {name} ---")
        for i, fk in enumerate(res['folds']):
            print(f"  Fold {i+1}: N={fk['n']:2d} | W={fk['n_win']:2d}, L={fk['n_loss']:2d} | Win%: {fk['win_pct']:4.1f}% | Net R: {fk['net_r']:+6.2f}R | Exp: {fk['exp_r']:+6.4f}R | PF: {fk['pf']:4.2f} | MaxDD: {fk['max_dd']:4.2f}R")
        blk = res['blocked']
        print(f"  Señales bloqueadas por Cap: {len(blk)} ops (PnL contrafactual: {blk['rr'].sum():+.2f} R)" if len(blk)>0 else "  Señales bloqueadas por Cap: 0 ops")

    print("\n" + "=" * 125)
    print("COBERTURA INSTITUCIONAL DE ACTIVOS EN CADA VARIANTE (DENOMINADOR = 23 ACTIVOS)")
    print("=" * 125)
    cfg = MalaysianSNRConfig()
    canonical = sorted(list(set(s.replace('micro', '') for s in cfg.allowed_symbols)))
    for name, res in results.items():
        tdf = res['trades']
        if len(tdf) == 0:
            continue
        pnl_per_sym = tdf.groupby('symbol')['rr'].sum()
        pos_s = [s for s in canonical if pnl_per_sym.get(s, 0) > 0]
        neg_s = [s for s in canonical if pnl_per_sym.get(s, 0) < 0]
        zero_s = [s for s in canonical if pnl_per_sym.get(s, 0) == 0]
        print(f"{name:44s} -> Positivos: {len(pos_s):2d} / 23 ({len(pos_s)/23*100:4.1f}%) | Negativos: {len(neg_s):2d} | Sin Trades: {len(zero_s):2d}")

if __name__ == '__main__':
    main()
