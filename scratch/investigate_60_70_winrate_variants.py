"""
scratch/investigate_60_70_winrate_variants.py
Investigación sistemática de variantes orientadas a un objetivo experimental de 60-70% de efectividad
en Malaysian SNR e ICT (Sabri Malle).

Métricas requeridas:
- Número de operaciones cerradas.
- % Ganadoras (> 0R), % Break-Even (== 0R), % Perdedoras (< 0R).
- Ganancia media (Avg Win), Pérdida media (Avg Loss), Payoff (Win/Loss).
- Expectativa neta en R, PnL neto en R.
- Profit Factor, Max Drawdown en R.
- Estabilidad walk-forward y sensibilidad a fricción.
- Separación estricta de conjuntos: Train (60%) vs Holdout OOS (40%) y Walk-Forward secuencial.
"""

import sys
from pathlib import Path
import pandas as pd
import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

def compute_detailed_kpis(rr_series: pd.Series, costs_slip_r: float = 0.0, gap_penalty_pct: float = 0.0) -> dict:
    if len(rr_series) == 0:
        return {
            "n": 0, "n_win": 0, "n_be": 0, "n_loss": 0,
            "wr_pct": 0.0, "be_pct": 0.0, "loss_pct": 0.0,
            "avg_win": 0.0, "avg_loss": 0.0, "payoff": 0.0,
            "exp_r": 0.0, "net_r": 0.0, "pf": 0.0, "max_dd": 0.0
        }
    
    # Adjust for costs/slippage/gaps
    adj_rr = rr_series.copy()
    if costs_slip_r > 0:
        adj_rr -= costs_slip_r
    if gap_penalty_pct > 0:
        # penalize losses by gap on SL
        loss_mask = adj_rr < 0
        adj_rr[loss_mask] -= (abs(adj_rr[loss_mask]) * gap_penalty_pct)
        
    n = len(adj_rr)
    wins = adj_rr[adj_rr > 0.001]
    bes = adj_rr[(adj_rr >= -0.001) & (adj_rr <= 0.001)]
    losses = adj_rr[adj_rr < -0.001]
    
    n_win = len(wins)
    n_be = len(bes)
    n_loss = len(losses)
    
    wr_pct = round(n_win / n * 100, 2)
    be_pct = round(n_be / n * 100, 2)
    loss_pct = round(n_loss / n * 100, 2)
    
    avg_win = round(float(wins.mean()), 3) if n_win > 0 else 0.0
    avg_loss = round(float(abs(losses.mean())), 3) if n_loss > 0 else 0.0
    payoff = round(avg_win / avg_loss, 3) if avg_loss > 0 else (99.0 if avg_win > 0 else 0.0)
    
    net_r = round(float(adj_rr.sum()), 2)
    exp_r = round(float(adj_rr.mean()), 4)
    
    tot_gain = float(wins.sum()) if n_win > 0 else 0.0
    tot_loss = float(abs(losses.sum())) if n_loss > 0 else 0.0
    pf = round(tot_gain / tot_loss, 3) if tot_loss > 0 else (99.0 if tot_gain > 0 else 0.0)
    
    cum = adj_rr.cumsum()
    dd = cum.cummax() - cum
    max_dd = round(float(dd.max()), 2) if len(dd) > 0 else 0.0
    
    return {
        "n": n, "n_win": n_win, "n_be": n_be, "n_loss": n_loss,
        "wr_pct": wr_pct, "be_pct": be_pct, "loss_pct": loss_pct,
        "avg_win": avg_win, "avg_loss": avg_loss, "payoff": payoff,
        "exp_r": exp_r, "net_r": net_r, "pf": pf, "max_dd": max_dd
    }

def analyze_snr():
    print("=" * 110)
    print("1. INVESTIGACIÓN DE EFECTIVIDAD 60-70% EN MALAYSIAN SNR (REPLAY FIEL M5)")
    print("=" * 110)
    
    df = pd.read_csv(PROJECT_ROOT / "storage" / "analysis" / "msnr_faithful_trades.csv")
    df['time'] = pd.to_datetime(df['time'], utc=True)
    df = df.sort_values('time').reset_index(drop=True)
    
    # Allowlist filter (23 canonical symbols)
    from strategy.malaysian_snr.config import MalaysianSNRConfig
    cfg = MalaysianSNRConfig()
    allowed = set(s.replace('micro', '') for s in cfg.allowed_symbols)
    df = df[df['symbol'].isin(allowed)].reset_index(drop=True)
    
    # Chronological Split (60% Train, 40% Holdout OOS)
    cutoff = pd.to_datetime('2026-05-18', utc=True)
    train_df = df[df['time'] < cutoff].copy()
    test_df = df[df['time'] >= cutoff].copy()
    
    print(f"Muestra Total Filtrada por Allowlist: {len(df)} trades | Fechas: {df['time'].min().strftime('%Y-%m-%d')} a {df['time'].max().strftime('%Y-%m-%d')}")
    print(f"Train (60%): N={len(train_df)} | Holdout OOS (40%): N={len(test_df)} (desde 2026-05-18)")
    
    # Base Holdout
    m_base = compute_detailed_kpis(test_df['rr'])
    
    # Causal nested asset selection (Assets with PnL > 0 in Train)
    train_sym_pnl = train_df.groupby('symbol')['rr'].sum()
    pos_syms = set(train_sym_pnl[train_sym_pnl > 0].index)
    test_causal = test_df[test_df['symbol'].isin(pos_syms)].copy()
    m_causal = compute_detailed_kpis(test_causal['rr'])
    
    # Variant 1: Causal + High Conviction ADX (ADX >= 25)
    test_v1 = test_causal[test_causal['adx'] >= 25.0]
    m_v1 = compute_detailed_kpis(test_v1['rr'])
    
    # Variant 2: Causal + Strict Body Ratio (body_ratio >= 0.60)
    test_v2 = test_causal[test_causal['body_ratio'] >= 0.60]
    m_v2 = compute_detailed_kpis(test_v2['rr'])
    
    # Variant 3: Causal + Escenario 1 Only (Continuación en activos con tendencia confirmada)
    test_v3 = test_causal[test_causal['scenario'] == 'ESC_1_CONTINUATION']
    m_v3 = compute_detailed_kpis(test_v3['rr'])
    
    # Variant 4: Causal + Escenario 2/3 (Reversión estructural limpia)
    test_v4 = test_causal[test_causal['scenario'].isin(['ESC_2_ENGULFING', 'ESC_3_FRACTAL', 'ESC_3_QUASIMODO'])]
    m_v4 = compute_detailed_kpis(test_v4['rr'])

    # Variant 5: Early TP Exit Simulation (Tomar TP a 1.0 R en vez de runner a 2.5-3.0 R)
    # Si trade ganó > 1.0 R, se computa como 1.0 R; si fue SL (-1.0 R), sigue como -1.0 R
    rr_tp1 = test_causal['rr'].copy()
    rr_tp1_capped = rr_tp1.apply(lambda r: 1.0 if r >= 1.0 else (r if r > 0 else -1.0))
    m_tp1 = compute_detailed_kpis(rr_tp1_capped)
    
    # Variant 6: Tight TP Exit (0.5 R TP para forzar Win Rate alto)
    rr_tp05_capped = rr_tp1.apply(lambda r: 0.5 if r >= 0.5 else (r if r > 0 else -1.0))
    m_tp05 = compute_detailed_kpis(rr_tp05_capped)

    print("\n--- COMPARATIVA EN HOLDOUT OOS (146 DÍAS) ---")
    variants = [
        ("Base Mecánica Pura", m_base),
        ("Selección Causal Dinámica", m_causal),
        ("Causal + ADX >= 25", m_v1),
        ("Causal + BodyRatio >= 0.60", m_v2),
        ("Causal + Solo Escenario 1", m_v3),
        ("Causal + Escenarios 2 y 3", m_v4),
        ("Causal + Salida Fija TP1 (1.0 R)", m_tp1),
        ("Causal + Salida Asimétrica (TP 0.5 R)", m_tp05),
    ]
    
    header = f"{'Variante':38s} | {'N':4s} | {'% Win':6s} | {'% BE':5s} | {'% Loss':6s} | {'AvgWin':6s} | {'AvgLoss':7s} | {'Payoff':6s} | {'Exp(R)':7s} | {'Net R':7s} | {'PF':5s} | {'MaxDD':6s}"
    print(header)
    print("-" * len(header))
    for name, m in variants:
        print(f"{name:38s} | {m['n']:4d} | {m['wr_pct']:5.1f}% | {m['be_pct']:4.1f}% | {m['loss_pct']:5.1f}% | {m['avg_win']:6.3f} | {m['avg_loss']:7.3f} | {m['payoff']:6.3f} | {m['exp_r']:+7.4f} | {m['net_r']:+7.2f} | {m['pf']:5.2f} | {m['max_dd']:6.2f}")

    return df

def analyze_ict():
    print("\n" + "=" * 110)
    print("2. INVESTIGACIÓN DE EFECTIVIDAD 60-70% EN ICT SABRI MALLE (REPLAY FIEL M5)")
    print("=" * 110)
    
    df = pd.read_csv(PROJECT_ROOT / "storage" / "analysis" / "ict_faithful_trades.csv")
    df['time'] = pd.to_datetime(df['time'], utc=True)
    df = df.sort_values('time').reset_index(drop=True)
    
    from config.strategy_config import PRUNED_ASSET_UNIVERSE
    canon = sorted(list(set(s.replace('micro', '') for s in PRUNED_ASSET_UNIVERSE['ICT'])))
    df = df[df['symbol'].isin(canon)].reset_index(drop=True)
    
    cutoff = pd.to_datetime('2026-05-18', utc=True)
    train_df = df[df['time'] < cutoff].copy()
    test_df = df[df['time'] >= cutoff].copy()
    
    m_base = compute_detailed_kpis(test_df['rr'])
    
    # Defensive filter
    defensive_mask = (test_df['symbol'] != 'Jump 25 Index') & (test_df['body_ratio'] > 0.50)
    test_def = test_df[defensive_mask].copy()
    m_def = compute_detailed_kpis(test_def['rr'])
    
    # Causal ex-ante: RiskExpansion <= 1.40 (approximated by risk_pct <= 0.20 on M5)
    test_risk = test_def[test_def['risk_pct'] <= 0.20].copy()
    m_risk = compute_detailed_kpis(test_risk['rr'])
    
    # Target R2 (exit at 2.0 R)
    m_r2 = compute_detailed_kpis(test_def['rr_r2'])
    
    # Target R1 (exit at 1.0 R)
    rr_r1 = test_def['rr'].apply(lambda r: 1.0 if r >= 1.0 else (r if r > 0 else -1.0))
    m_r1 = compute_detailed_kpis(rr_r1)
    
    print("\n--- COMPARATIVA EN HOLDOUT OOS ICT (146 DÍAS) ---")
    variants = [
        ("Base Mecánica Canónica", m_base),
        ("Defensivo (Excl Jump25 + Body>0.50)", m_def),
        ("Defensivo + Riesgo Acotado (risk<=0.20%)", m_risk),
        ("Defensivo + Salida Fija TP 2.0 R", m_r2),
        ("Defensivo + Salida Temprana TP 1.0 R", m_r1),
    ]
    
    header = f"{'Variante':40s} | {'N':4s} | {'% Win':6s} | {'% BE':5s} | {'% Loss':6s} | {'AvgWin':6s} | {'AvgLoss':7s} | {'Payoff':6s} | {'Exp(R)':7s} | {'Net R':7s} | {'PF':5s} | {'MaxDD':6s}"
    print(header)
    print("-" * len(header))
    for name, m in variants:
        print(f"{name:40s} | {m['n']:4d} | {m['wr_pct']:5.1f}% | {m['be_pct']:4.1f}% | {m['loss_pct']:5.1f}% | {m['avg_win']:6.3f} | {m['avg_loss']:7.3f} | {m['payoff']:6.3f} | {m['exp_r']:+7.4f} | {m['net_r']:+7.2f} | {m['pf']:5.2f} | {m['max_dd']:6.2f}")

if __name__ == '__main__':
    analyze_snr()
    analyze_ict()
