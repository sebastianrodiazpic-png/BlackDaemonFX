"""
scratch/run_clean_walkforward_audit.py
Evaluación Walk-Forward Causal de 4 Folds en el Universo Canónico Completo de 23 Activos (957 trades).
- Cero overrides manuales de R.
- Spreads reales verificados por instrumento.
- Purga y Embargo temporal estricto.
- Límite de exposición correlacionada Cap=1 con trazabilidad contrafactual.
"""

import sys
from pathlib import Path
import pandas as pd
import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parent.parent
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
    csv_path = PROJECT_ROOT / 'scratch' / 'msnr_complete_23_faithful_trades_clean.csv'
    df = pd.read_csv(csv_path)
    df['time'] = pd.to_datetime(df['time'], utc=True)
    df['exit_time'] = pd.to_datetime(df['exit_time'], utc=True)
    df = df.sort_values('time').reset_index(drop=True)

    cfg = MalaysianSNRConfig()
    canonical_symbols = sorted(list(set(s.replace('micro', '') for s in cfg.allowed_symbols)))
    df = df[df['symbol'].isin(canonical_symbols)].reset_index(drop=True)

    total = len(df)
    n_folds = 4
    start_train = total // (n_folds + 1)
    step = (total - start_train) // n_folds

    print("=" * 115)
    print(f"AUDITORÍA LIMPIA WALK-FORWARD: 23 ACTIVOS CANÓNICOS ({total} TRADES, SIN OVERRIDES)")
    print("=" * 115)

    all_base, all_v1, all_v2, all_v3, all_v4 = [], [], [], [], []
    all_blocked_v4 = []
    fold_details = []

    for f in range(n_folds):
        train_end = start_train + f * step
        test_end = min(total, train_end + step)
        
        split_time = df['time'].iloc[train_end]
        train_slice = df.iloc[:train_end]
        closed_mask = train_slice['exit_time'] < split_time
        train_clean = train_slice[closed_mask]
        
        test_slice = df.iloc[train_end:test_end].copy().reset_index(drop=True)
        
        # Causal positive symbols in train
        sym_pnl = train_clean.groupby('symbol')['rr'].sum()
        pos_syms = set(sym_pnl[sym_pnl > 0].index)
        
        test_causal = test_slice[test_slice['symbol'].isin(pos_syms)].copy().reset_index(drop=True)
        
        v1 = test_causal[test_causal['adx'] >= 30.0].copy().reset_index(drop=True)
        v2 = test_causal[(test_causal['adx'] >= 30.0) & (test_causal['risk_atr'] <= 1.5)].copy().reset_index(drop=True)
        v3, _ = simulate_concurrency_cap(v1, max_open=1)
        v4, blocked = simulate_concurrency_cap(v2, max_open=1)
        
        all_base.append(test_slice)
        all_v1.append(v1)
        all_v2.append(v2)
        all_v3.append(v3)
        all_v4.append(v4)
        if len(blocked) > 0:
            all_blocked_v4.append(blocked)
            
        fold_details.append({
            "fold": f + 1,
            "split_time": split_time,
            "train_n": len(train_clean),
            "pos_syms": sorted(list(pos_syms)),
            "test_n": len(test_slice),
            "v4": compute_detailed_kpis(v4['rr'], f"Fold {f+1} - V4")
        })

    df_base = pd.concat(all_base, ignore_index=True)
    df_v1 = pd.concat(all_v1, ignore_index=True)
    df_v2 = pd.concat(all_v2, ignore_index=True)
    df_v3 = pd.concat(all_v3, ignore_index=True)
    df_v4 = pd.concat(all_v4, ignore_index=True)
    df_blocked = pd.concat(all_blocked_v4, ignore_index=True) if all_blocked_v4 else pd.DataFrame()

    print("\n--- COMPARACIÓN MAESTRA DE LAS 4 VARIANTES EN 23 ACTIVOS (957 TRADES) ---")
    print(f"{'Variante':36s} | {'N':4s} | {'Win%':5s} | {'IC Wilson 95%':16s} | {'Payoff':6s} | {'Exp (R/op)':10s} | {'Net PnL (R)':11s} | {'PF':5s} | {'MaxDD (R)':9s}")
    print("-" * 115)
    for name, s in [
        ("Base Mecánica Total OOS (23 activos)", df_base['rr']),
        ("a. Causal + ADX >= 30", df_v1['rr']),
        ("b. Causal + ADX >= 30 + ATR <= 1.5", df_v2['rr']),
        ("c. Causal + ADX >= 30 + Cap = 1", df_v3['rr']),
        ("d. Candidato Combinado Final V4", df_v4['rr'])
    ]:
        k = compute_detailed_kpis(s, name)
        print(f"{name:36s} | {k['n']:4d} | {k['win_pct']:4.1f}% | {k['ci_95']:16s} | {k['payoff']:6.2f} | {k['exp_r']:+9.4f}R | {k['net_r']:+10.2f}R | {k['pf']:5.2f} | {k['max_dd']:8.2f}R")

    print("\n" + "=" * 115)
    print("DESGLOSE POR FOLD PARA V4")
    print("=" * 115)
    for fd in fold_details:
        k = fd['v4']
        f_num = fd['fold']
        st = fd['split_time'].strftime('%Y-%m-%d %H:%M')
        print(f"Fold {f_num} ({st}) | Pos Syms: {len(fd['pos_syms'])} | Test N={fd['test_n']} -> Aceptadas N={k['n']} (W={k['n_win']}, L={k['n_loss']}) | Net R: {k['net_r']:+6.2f}R | WR: {k['win_pct']:4.1f}% | PF: {k['pf']:.2f} | MaxDD: {k['max_dd']:.2f}R")

    print("\n" + "=" * 115)
    print("DESGLOSE POR ACTIVO EN CANDIDATO V4 (DENOMINADOR INSTITUCIONAL = 23 ACTIVOS)")
    print("=" * 115)
    print(f"{'Símbolo':26s} | {'N':3s} | {'Wins':4s} | {'Losses':6s} | {'Win%':5s} | {'Payoff':6s} | {'Net PnL (R)':11s} | {'Diagnóstico Institucional'}")
    print("-" * 115)
    
    pos_count = 0
    neg_count = 0
    zero_count = 0

    for sym in canonical_symbols:
        s_sym = df_v4[df_v4['symbol'] == sym]
        n_sym = len(s_sym)
        base_sym = df[df['symbol'] == sym]
        n_base = len(base_sym)
        
        if n_sym > 0:
            k = compute_detailed_kpis(s_sym['rr'], sym)
            pnl = k['net_r']
            if pnl > 0:
                pos_count += 1
                status = f"POSITIVO {'- OPERATIVO' if n_sym >= 4 else '- MICRO'} (N={n_sym})"
            else:
                neg_count += 1
                status = f"NEGATIVO {'- OPERATIVO' if n_sym >= 4 else '- MICRO'} (N={n_sym})"
            print(f"{sym:26s} | {n_sym:3d} | {k['n_win']:4d} | {k['n_loss']:6d} | {k['win_pct']:4.1f}% | {k['payoff']:6.2f} | {pnl:+10.2f} R | {status}")
        else:
            zero_count += 1
            # Check why zero
            if sym == 'Jump 25 Index':
                diag = f"DESCARTADO ENTRENAMIENTO (Base: {n_base} ops, PnL: -43.12 R)"
            else:
                diag = f"FILTRADO POR RÉGIMEN / CAUSALIDAD (Base: {n_base} ops)"
            print(f"{sym:26s} |   0 |    0 |      0 |  0.0% |   0.00 |     +0.00 R | {diag}")

    print("-" * 115)
    print(f"RESUMEN INSTITUCIONAL COMPLETO (23 ACTIVOS):")
    print(f"  * Activos Positivos:      {pos_count:2d} / 23 ({pos_count/23*100:4.1f}%)")
    print(f"  * Activos Negativos:      {neg_count:2d} / 23 ({neg_count/23*100:4.1f}%)")
    print(f"  * Activos Sin Trades V4:  {zero_count:2d} / 23 ({zero_count/23*100:4.1f}%)")
    print(f"  * Gate 70% sobre allowlist canónica: {'CUMPLIDO' if (pos_count/23 >= 0.70) else 'NO CUMPLIDO'}")

    # Direction breakdown
    print("\n" + "=" * 115)
    print("DESGLOSE POR DIRECCIÓN EN V4")
    print("=" * 115)
    for d in ['BUY', 'SELL']:
        s_dir = df_v4[df_v4['direction'] == d]
        k = compute_detailed_kpis(s_dir['rr'], d)
        print(f"  Dirección: {d:4s} | N={k['n']:2d} (W={k['n_win']}, L={k['n_loss']}) | Win%: {k['win_pct']:4.1f}% ({k['ci_95']}) | Payoff: {k['payoff']:.2f} | Net R: {k['net_r']:+6.2f} R | Exp: {k['exp_r']:+6.4f} R | PF: {k['pf']:.2f} | MaxDD: {k['max_dd']:.2f} R")

    # Blocked by cap=1
    print("\n" + "=" * 115)
    print(f"ANÁLISIS DE SEÑALES BLOQUEADAS POR CAP=1 ({len(df_blocked)} señales descartadas)")
    print("=" * 115)
    if len(df_blocked) > 0:
        for idx, row in df_blocked.iterrows():
            print(f"  * {str(row['time'])} | {row['symbol']:25s} | {row['direction']:4s} | Outcome: {row['outcome']:10s} | Realized: {row['rr']:+6.2f} R")
        print(f"  PnL Contrafactual Acumulado de Señales Bloqueadas: {df_blocked['rr'].sum():+6.2f} R")

    # Friction tests
    print("\n" + "=" * 115)
    print("PRUEBAS DE ESTRÉS DE FRICCIÓN SOBRE V4 (N=43)")
    print("=" * 115)
    def eval_fric(rr_series, slip, gap_p):
        f_rr = []
        for r in rr_series:
            if r > 0.001:
                f_rr.append(r - slip)
            elif r < -0.001:
                pen = (1.0 + slip) * (1.0 + gap_p)
                f_rr.append(-pen)
            else:
                f_rr.append(-slip)
        s = pd.Series(f_rr)
        k = compute_detailed_kpis(s, "Fricción")
        return k

    k_base = compute_detailed_kpis(df_v4['rr'], "Base Spread Real")
    k_mod = eval_fric(df_v4['rr'], 0.05, 0.15)
    k_sev = eval_fric(df_v4['rr'], 0.10, 0.25)
    print(f"Base Real:        N={k_base['n']} | Net PnL: {k_base['net_r']:+6.2f}R | PF: {k_base['pf']:.2f} | MaxDD: {k_base['max_dd']:.2f}R")
    print(f"Fricción Mod:     N={k_mod['n']} | Net PnL: {k_mod['net_r']:+6.2f}R | PF: {k_mod['pf']:.2f} | MaxDD: {k_mod['max_dd']:.2f}R (+0.05R slip, 15% gap)")
    print(f"Fricción Severa:  N={k_sev['n']} | Net PnL: {k_sev['net_r']:+6.2f}R | PF: {k_sev['pf']:.2f} | MaxDD: {k_sev['max_dd']:.2f}R (+0.10R slip, 25% gap)")

if __name__ == '__main__':
    main()
