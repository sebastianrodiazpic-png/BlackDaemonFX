"""
scratch/compute_winrate_frontier_and_ci.py
Cálculo riguroso de la frontera entre Efectividad (Win Rate) y Rentabilidad Neta (PnL en R),
con intervalos de confianza de Wilson al 95%, métricas de payoff y análisis de salidas.
"""

import sys
from pathlib import Path
import pandas as pd
import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

def wilson_score_interval(k: int, n: int, confidence: float = 0.95) -> tuple:
    if n == 0:
        return (0.0, 0.0)
    z = 1.95996  # 95% confidence
    p_hat = k / n
    denom = 1 + (z**2) / n
    center = (p_hat + (z**2) / (2 * n)) / denom
    margin = (z * np.sqrt((p_hat * (1 - p_hat) + (z**2) / (4 * n)) / n)) / denom
    lower = max(0.0, center - margin)
    upper = min(1.0, center + margin)
    return (round(lower * 100, 1), round(upper * 100, 1))

def run_frontier_analysis():
    print("=" * 115)
    print("FRONTERA EFECTIVIDAD VS. RENTABILIDAD NETA EN MALAYSIAN SNR (HOLDOUT OOS 146 DÍAS)")
    print("=" * 115)
    
    df = pd.read_csv(PROJECT_ROOT / "storage" / "analysis" / "msnr_faithful_trades.csv")
    df['time'] = pd.to_datetime(df['time'], utc=True)
    df = df.sort_values('time').reset_index(drop=True)
    
    from strategy.malaysian_snr.config import MalaysianSNRConfig
    cfg = MalaysianSNRConfig()
    allowed = set(s.replace('micro', '') for s in cfg.allowed_symbols)
    df = df[df['symbol'].isin(allowed)].reset_index(drop=True)
    
    cutoff = pd.to_datetime('2026-05-18', utc=True)
    train_df = df[df['time'] < cutoff].copy()
    test_df = df[df['time'] >= cutoff].copy()
    
    train_sym_pnl = train_df.groupby('symbol')['rr'].sum()
    pos_syms = set(train_sym_pnl[train_sym_pnl > 0].index)
    test_causal = test_df[test_df['symbol'].isin(pos_syms)].copy()
    
    variants = [
        ("1. Base Mecánica Pura", test_df),
        ("2. Selección Causal Dinámica", test_causal),
        ("3. Causal + ADX >= 20", test_causal[test_causal['adx'] >= 20.0]),
        ("4. Causal + ADX >= 25", test_causal[test_causal['adx'] >= 25.0]),
        ("5. Causal + ADX >= 30", test_causal[test_causal['adx'] >= 30.0]),
        ("6. Causal + ADX >= 30 + Body >= 0.60", test_causal[(test_causal['adx'] >= 30.0) & (test_causal['body_ratio'] >= 0.60)]),
        ("7. Causal + ADX >= 30 + Body >= 0.70 + ATR <= 1.5", test_causal[(test_causal['adx'] >= 30.0) & (test_causal['body_ratio'] >= 0.70) & (test_causal['risk_atr'] <= 1.5)]),
        ("8. Micro-Muestra: Step+Boom1000 (Esc 1)", test_causal[(test_causal['scenario'] == 'ESC_1_CONTINUATION') & (test_causal['symbol'].isin(['Step Index', 'Boom 1000 Index']))]),
    ]
    
    rows = []
    for name, sub in variants:
        n = len(sub)
        if n == 0:
            continue
        wins = sub[sub['rr'] > 0.001]
        bes = sub[(sub['rr'] >= -0.001) & (sub['rr'] <= 0.001)]
        losses = sub[sub['rr'] < -0.001]
        
        k_win = len(wins)
        k_be = len(bes)
        k_loss = len(losses)
        
        wr_pct = round(k_win / n * 100, 1)
        be_pct = round(k_be / n * 100, 1)
        loss_pct = round(k_loss / n * 100, 1)
        
        ci_low, ci_high = wilson_score_interval(k_win, n)
        
        avg_w = round(float(wins['rr'].mean()), 2) if k_win > 0 else 0.0
        avg_l = round(float(abs(losses['rr'].mean())), 2) if k_loss > 0 else 0.0
        payoff = round(avg_w / avg_l, 2) if avg_l > 0 else (99.0 if avg_w > 0 else 0.0)
        
        exp_r = round(float(sub['rr'].mean()), 4)
        net_r = round(float(sub['rr'].sum()), 2)
        
        tot_g = float(wins['rr'].sum()) if k_win > 0 else 0.0
        tot_l = float(abs(losses['rr'].sum())) if k_loss > 0 else 0.0
        pf = round(tot_g / tot_l, 2) if tot_l > 0 else (99.0 if tot_g > 0 else 0.0)
        
        cum = sub['rr'].cumsum()
        max_dd = round(float((cum.cummax() - cum).max()), 2) if len(cum) > 0 else 0.0
        
        # Trade sacrifice vs Base
        trade_loss_pct = round((len(test_df) - n) / len(test_df) * 100, 1)
        
        rows.append({
            "Variante": name, "N": n, "Sacrificio": f"-{trade_loss_pct}%",
            "Win%": f"{wr_pct}%", "IC 95%": f"[{ci_low}%, {ci_high}%]",
            "BE%": f"{be_pct}%", "Loss%": f"{loss_pct}%",
            "AvgW": avg_w, "AvgL": avg_l, "Payoff": payoff,
            "Exp(R)": exp_r, "Net R": net_r, "PF": pf, "MaxDD": max_dd
        })
        
    res_df = pd.DataFrame(rows)
    print(res_df.to_string(index=False))

    # Exit simulation on variant 6 (ADX >= 30, Body >= 0.60, N=56)
    print("\n" + "=" * 115)
    print("ANÁLISIS DE GESTIÓN Y SALIDAS SOBRE VARIANTE DE MAYOR PNL (N=56, NET R = +23.65 R)")
    print("=" * 115)
    sub56 = test_causal[(test_causal['adx'] >= 30.0) & (test_causal['body_ratio'] >= 0.60)].copy()
    
    # Base exit (runner 2.0-3.0R)
    rr_base = sub56['rr']
    
    # Cap at TP 1.5R
    rr_tp15 = rr_base.apply(lambda r: 1.5 if r >= 1.5 else (r if r > 0 else -1.0))
    # Cap at TP 1.0R
    rr_tp10 = rr_base.apply(lambda r: 1.0 if r >= 1.0 else (r if r > 0 else -1.0))
    # Cap at TP 0.5R
    rr_tp05 = rr_base.apply(lambda r: 0.5 if r >= 0.5 else (r if r > 0 else -1.0))
    
    exit_variants = [
        ("Base (Salida Original Runner 2.0-3.0R)", rr_base),
        ("Salida Capped TP 1.5 R", rr_tp15),
        ("Salida Capped TP 1.0 R", rr_tp10),
        ("Salida Capped TP 0.5 R", rr_tp05),
    ]
    
    exit_rows = []
    for ename, s_rr in exit_variants:
        n = len(s_rr)
        wins = s_rr[s_rr > 0.001]
        losses = s_rr[s_rr < -0.001]
        kw = len(wins)
        kl = len(losses)
        wr = round(kw / n * 100, 1)
        aw = round(float(wins.mean()), 2) if kw > 0 else 0.0
        al = round(float(abs(losses.mean())), 2) if kl > 0 else 0.0
        po = round(aw / al, 2) if al > 0 else 0.0
        net = round(float(s_rr.sum()), 2)
        exp = round(float(s_rr.mean()), 4)
        tg = float(wins.sum()) if kw > 0 else 0.0
        tl = float(abs(losses.sum())) if kl > 0 else 0.0
        pf = round(tg / tl, 2) if tl > 0 else 0.0
        cum = s_rr.cumsum()
        mdd = round(float((cum.cummax() - cum).max()), 2) if len(cum) > 0 else 0.0
        
        exit_rows.append({
            "Esquema de Salida": ename, "N": n, "Win%": f"{wr}%",
            "AvgWin": aw, "AvgLoss": al, "Payoff": po,
            "Exp (R)": exp, "Net PnL (R)": net, "PF": pf, "MaxDD": mdd
        })
    print(pd.DataFrame(exit_rows).to_string(index=False))

if __name__ == '__main__':
    run_frontier_analysis()
