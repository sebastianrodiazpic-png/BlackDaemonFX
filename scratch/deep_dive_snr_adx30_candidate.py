"""
scratch/deep_dive_snr_adx30_candidate.py
Auditoría forense del candidato prioritario: Malaysian SNR Causal + ADX >= 30.
Desglose por activo, dirección, sub-ventanas temporales, límites de concurrencia,
ablaciones de filtros ex ante y sensibilidad a fricción.
"""

import sys
from pathlib import Path
import pandas as pd
import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from strategy.malaysian_snr.config import MalaysianSNRConfig

def compute_kpis(series: pd.Series, label: str = "") -> dict:
    n = len(series)
    if n == 0:
        return {"label": label, "n": 0, "win_pct": 0.0, "be_pct": 0.0, "loss_pct": 0.0,
                "avg_win": 0.0, "avg_loss": 0.0, "payoff": 0.0,
                "exp_r": 0.0, "net_r": 0.0, "pf": 0.0, "max_dd": 0.0}
    
    wins = series[series > 0.001]
    bes = series[(series >= -0.001) & (series <= 0.001)]
    losses = series[series < -0.001]
    
    nw, nb, nl = len(wins), len(bes), len(losses)
    wr = round(nw / n * 100, 2)
    be_r = round(nb / n * 100, 2)
    loss_r = round(nl / n * 100, 2)
    
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
        "label": label, "n": n, "win_pct": wr, "be_pct": be_r, "loss_pct": loss_r,
        "avg_win": aw, "avg_loss": al, "payoff": payoff,
        "exp_r": exp_r, "net_r": net_r, "pf": pf, "max_dd": max_dd
    }

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

def run_deep_dive():
    print("=" * 110)
    print("AUDITORÍA FORENSE: MALAYSIAN SNR CANDIDATO CAUSAL + ADX >= 30 (N=81)")
    print("=" * 110)
    
    df = pd.read_csv(PROJECT_ROOT / "storage" / "analysis" / "msnr_faithful_trades.csv")
    df['time'] = pd.to_datetime(df['time'], utc=True)
    df = df.sort_values('time').reset_index(drop=True)
    df['exit_time'] = df['time'] + pd.to_timedelta(df['bars'] * 15, unit='m')
    
    cfg = MalaysianSNRConfig()
    allowed = set(s.replace('micro', '') for s in cfg.allowed_symbols)
    df = df[df['symbol'].isin(allowed)].reset_index(drop=True)
    
    cutoff = pd.to_datetime('2026-05-18', utc=True)
    train_df = df[df['time'] < cutoff].copy()
    test_df = df[df['time'] >= cutoff].copy()
    
    # Causal asset selection from train
    train_pnl = train_df.groupby('symbol')['rr'].sum()
    pos_syms = set(train_pnl[train_pnl > 0].index)
    test_causal = test_df[test_df['symbol'].isin(pos_syms)].copy()
    
    # Candidate: Causal + ADX >= 30
    cand = test_causal[test_causal['adx'] >= 30.0].copy().reset_index(drop=True)
    
    k_cand = compute_kpis(cand['rr'], "Candidato ADX >= 30")
    print(f"Verificación Candidato: N={k_cand['n']} | WR={k_cand['win_pct']}% | Net R={k_cand['net_r']} R | Exp={k_cand['exp_r']} R | PF={k_cand['pf']} | MaxDD={k_cand['max_dd']} R")
    print(f"Activos Seleccionados desde Train ({len(pos_syms)}): {sorted(list(pos_syms))}")
    
    # 1. Breakdown by Asset
    print("\n" + "-" * 110)
    print("1. DESGLOSE POR ACTIVO EN CANDIDATO (N=81)")
    print("-" * 110)
    sym_rows = []
    for sym, grp in cand.groupby('symbol'):
        k = compute_kpis(grp['rr'], sym)
        sym_rows.append(k)
    sym_df = pd.DataFrame(sym_rows)
    print(sym_df[['label', 'n', 'win_pct', 'avg_win', 'avg_loss', 'payoff', 'net_r', 'exp_r', 'pf', 'max_dd']].to_string(index=False))
    
    # 2. Breakdown by Direction (BUY vs SELL)
    print("\n" + "-" * 110)
    print("2. DESGLOSE POR DIRECCIÓN (BUY vs SELL)")
    print("-" * 110)
    dir_rows = []
    for d, grp in cand.groupby('direction'):
        k = compute_kpis(grp['rr'], d)
        dir_rows.append(k)
    dir_df = pd.DataFrame(dir_rows)
    print(dir_df[['label', 'n', 'win_pct', 'avg_win', 'avg_loss', 'payoff', 'net_r', 'exp_r', 'pf', 'max_dd']].to_string(index=False))
    
    # 3. Breakdown by Temporal Sub-Windows
    print("\n" + "-" * 110)
    print("3. DESGLOSE POR VENTANA TEMPORAL DENTRO DEL HOLDOUT OOS")
    print("-" * 110)
    t_min = cand['time'].min()
    t_max = cand['time'].max()
    t_delta = (t_max - t_min) / 3
    
    w1_end = t_min + t_delta
    w2_end = t_min + 2 * t_delta
    
    w1 = cand[cand['time'] < w1_end]
    w2 = cand[(cand['time'] >= w1_end) & (cand['time'] < w2_end)]
    w3 = cand[cand['time'] >= w2_end]
    
    w_rows = [
        compute_kpis(w1['rr'], f"Ventana 1 ({t_min.strftime('%m/%d')} - {w1_end.strftime('%m/%d')})"),
        compute_kpis(w2['rr'], f"Ventana 2 ({w1_end.strftime('%m/%d')} - {w2_end.strftime('%m/%d')})"),
        compute_kpis(w3['rr'], f"Ventana 3 ({w2_end.strftime('%m/%d')} - {t_max.strftime('%m/%d')})")
    ]
    w_df = pd.DataFrame(w_rows)
    print(w_df[['label', 'n', 'win_pct', 'avg_win', 'avg_loss', 'payoff', 'net_r', 'exp_r', 'pf', 'max_dd']].to_string(index=False))
    
    # 4. Simulation of Position Concurrency Caps
    print("\n" + "-" * 110)
    print("4. SIMULACIÓN DE LÍMITES DE CONCURRENCIA DE POSICIONES (REGLAS DE EJECUCIÓN)")
    print("-" * 110)
    
    cand_cap1 = None
    for cap in [99, 3, 2, 1]:
        sim_df = simulate_concurrency_cap(cand, max_open=cap)
        if cap == 1:
            cand_cap1 = sim_df.copy()
        k = compute_kpis(sim_df['rr'], f"Cap Concurrencia = {cap if cap < 90 else 'Ilimitado'}")
        k['skipped'] = len(cand) - len(sim_df)
        print(f"  {k['label']:25s} | Trades: {k['n']:2d} (Descartados: {k['skipped']:2d}) | WR: {k['win_pct']:4.1f}% | Net: {k['net_r']:+6.2f} R | Exp: {k['exp_r']:+6.4f} R | PF: {k['pf']:4.2f} | MaxDD: {k['max_dd']:5.2f} R")

    # 5. Ex-Ante Filter Ablations on Top of ADX >= 30
    print("\n" + "-" * 110)
    print("5. ABLACIONES DE FILTROS EX ANTE ADICIONALES SOBRE ADX >= 30")
    print("-" * 110)
    
    cand_atr = cand[cand['risk_atr'] <= 1.5].copy()
    ablation_sets = [
        ("Base ADX >= 30", cand),
        ("+ Body Ratio >= 0.55", cand[cand['body_ratio'] >= 0.55]),
        ("+ Body Ratio >= 0.60", cand[cand['body_ratio'] >= 0.60]),
        ("+ ATR Risk <= 1.5", cand_atr),
        ("+ Solo BUY (Alineación alcista)", cand[cand['direction'] == 'BUY']),
        ("+ Solo SELL (Alineación bajista)", cand[cand['direction'] == 'SELL']),
        ("+ Excluir horas nocturnas (00-06 UTC)", cand[~cand['hour_utc'].isin([0, 1, 2, 3, 4, 5, 6])]),
    ]
    
    abl_rows = []
    for aname, adf in ablation_sets:
        k = compute_kpis(adf['rr'], aname)
        k['sacrifice_pct'] = round((len(cand) - len(adf)) / len(cand) * 100, 1)
        abl_rows.append(k)
    abl_df = pd.DataFrame(abl_rows)
    print(abl_df[['label', 'n', 'sacrifice_pct', 'win_pct', 'payoff', 'net_r', 'exp_r', 'pf', 'max_dd']].to_string(index=False))

    # 6. Stress Testing Execution & Friction
    print("\n" + "-" * 110)
    print("6. MATRIZ DE ESTRÉS DE EJECUCIÓN (SLIPPAGE Y GAPS)")
    print("-" * 110)
    
    stress_scenarios = [
        ("Base (Spread Deriv Real)", 0.0, 0.0),
        ("Fricción Baja (+0.025 R slip + 10% gap)", 0.025, 0.10),
        ("Fricción Moderada (+0.05 R slip + 15% gap)", 0.05, 0.15),
        ("Fricción Severa (+0.10 R slip + 20% gap)", 0.10, 0.20),
    ]
    
    for name, sub in [("Base ADX >= 30 (Ilimitado, N=81)", cand), 
                      ("Cap Concurrencia = 1 (N=61)", cand_cap1),
                      ("Filtro ATR Risk <= 1.5 (N=49)", cand_atr)]:
        print(f"\n  >>> VARIANTE: {name}")
        for sname, slip_r, gap_pct in stress_scenarios:
            rr_adj = sub['rr'].copy()
            if slip_r > 0:
                rr_adj -= slip_r
            if gap_pct > 0:
                losses_mask = rr_adj < 0
                rr_adj[losses_mask] -= (abs(rr_adj[losses_mask]) * gap_pct)
            k = compute_kpis(rr_adj, sname)
            print(f"    {sname:44s} | Net R = {k['net_r']:+6.2f} R | Exp = {k['exp_r']:+6.4f} R | PF = {k['pf']:4.2f} | MaxDD = {k['max_dd']:5.2f} R")

if __name__ == '__main__':
    run_deep_dive()
