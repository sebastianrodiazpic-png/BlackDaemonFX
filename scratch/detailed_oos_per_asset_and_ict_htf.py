"""Auditoría detallada por activo para SNR (Step, Boom 1000, Crash 1000, XAUUSD)
y evaluación experimental de contexto HTF H1/H4 con RiskExpansion en ICT.
Ejecución en modo de solo lectura sobre datasets locales.
"""

import sys
from pathlib import Path
import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Windows UTF-8
for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

from config.strategy_config import PRUNED_ASSET_UNIVERSE
from strategy.malaysian_snr.config import MalaysianSNRConfig

def compute_metrics(rr_series: pd.Series) -> dict:
    if len(rr_series) == 0:
        return {"trades": 0, "wr": 0.0, "net_r": 0.0, "exp_r": 0.0, "pf": 0.0, "max_dd_r": 0.0, "gross_win": 0.0, "gross_loss": 0.0}
    trades = len(rr_series)
    wins = rr_series[rr_series > 0]
    losses = rr_series[rr_series <= 0]
    wr = len(wins) / trades * 100
    net_r = float(rr_series.sum())
    exp_r = float(rr_series.mean())
    gain = float(wins.sum()) if len(wins) > 0 else 0.0
    loss = float(abs(losses.sum())) if len(losses) > 0 else 0.0
    pf = (gain / loss) if loss > 0 else (99.0 if gain > 0 else 0.0)
    
    cum_r = rr_series.cumsum()
    dd = cum_r.cummax() - cum_r
    max_dd = float(dd.max()) if len(dd) > 0 else 0.0
    return {
        "trades": trades,
        "wr": round(wr, 2),
        "net_r": round(net_r, 2),
        "exp_r": round(exp_r, 4),
        "pf": round(pf, 3),
        "max_dd_r": round(max_dd, 2),
        "gross_win": round(gain, 2),
        "gross_loss": round(loss, 2)
    }

def audit_snr_individual_assets():
    print("=" * 80)
    print("AUDITORÍA DE ACTIVOS TENDENCIALES EN MALAYSIAN SNR: STEP, BOOM 1000, CRASH 1000, XAUUSD")
    print("=" * 80)
    
    df = pd.read_csv(PROJECT_ROOT / "storage" / "analysis" / "msnr_faithful_trades.csv")
    df['time'] = pd.to_datetime(df['time'], utc=True)
    df = df.sort_values('time').reset_index(drop=True)
    df['exit_time'] = df['time'] + pd.to_timedelta(df['bars'] * 15, unit='m')
    
    # Holdout 40%
    split_idx = int(len(df) * 0.60)
    split_time = df['time'].iloc[split_idx]
    train_df = df.iloc[:split_idx].copy()
    test_df = df.iloc[split_idx:].copy().reset_index(drop=True)
    
    target_assets = ['Step Index', 'Boom 1000 Index', 'Crash 1000 Index', 'XAUUSD']
    
    print(f"\n1. Rendimiento Individual en Holdout OOS (146 días, N total={len(test_df)}):")
    print(f"{'Activo':20s} | {'Base N':6s} | {'Base Net R':10s} | {'Base PF':7s} | {'Causal N':8s} | {'Causal Net R':12s} | {'Causal PF':9s} | {'Causal MaxDD':12s}")
    print("-" * 95)
    
    # Causal rule learned in Train:
    # Train performance per asset:
    train_esc1_perf = train_df[train_df['scenario'] == 'ESC_1_CONTINUATION'].groupby('symbol')['rr'].sum()
    causal_allowed_esc1 = train_esc1_perf[train_esc1_perf > 0].index.tolist()
    
    total_base_target_r = 0.0
    total_causal_target_r = 0.0
    
    for sym in target_assets:
        base_sub = test_df[test_df['symbol'] == sym]
        m_base = compute_metrics(base_sub['rr'])
        
        # Causal variant: body_ratio >= 0.50, adx >= 20, Escenario 1 allowed if sym in causal_allowed_esc1
        causal_mask = (test_df['symbol'] == sym) & (test_df['body_ratio'] >= 0.50) & (test_df['adx'] >= 20.0)
        if sym not in causal_allowed_esc1:
            causal_mask = causal_mask & (test_df['scenario'] != 'ESC_1_CONTINUATION')
            
        causal_sub = test_df[causal_mask]
        m_causal = compute_metrics(causal_sub['rr'])
        
        total_base_target_r += m_base['net_r']
        total_causal_target_r += m_causal['net_r']
        
        print(f"{sym:20s} | {m_base['trades']:6d} | {m_base['net_r']:+9.2f}R | {m_base['pf']:7.3f} | {m_causal['trades']:8d} | {m_causal['net_r']:+11.2f}R | {m_causal['pf']:9.3f} | {m_causal['max_dd_r']:11.2f}R")
        
    print("-" * 95)
    print(f"{'TOTAL 4 ACTIVOS':20s} | {total_base_target_r:+9.2f}R | {'-':7s} | {'-':8s} | {total_causal_target_r:+11.2f}R | {'-':9s} | {'-':12s}")
    
    # Detalle de Escenario 1 en Holdout para estos 4 activos
    print("\n2. Detalle de Escenario 1 (Continuación) en Holdout OOS:")
    for sym in target_assets:
        esc1_sub = test_df[(test_df['symbol'] == sym) & (test_df['scenario'] == 'ESC_1_CONTINUATION')]
        m_esc1 = compute_metrics(esc1_sub['rr'])
        print(f"  - {sym:18s}: N={m_esc1['trades']:2d} | Net R={m_esc1['net_r']:+6.2f}R | PF={m_esc1['pf']:5.3f} | WR={m_esc1['wr']:5.1f}%")

def audit_ict_htf_and_regime():
    print("\n" + "=" * 80)
    print("EVALUACIÓN DE ICT: RISK EXPANSION + CONTEXTO H1/H4 (EXPERIMENTO EN SCRATCH)")
    print("=" * 80)
    
    df = pd.read_csv(PROJECT_ROOT / "storage" / "analysis" / "ict_faithful_trades.csv")
    df['time'] = pd.to_datetime(df['time'], utc=True)
    df = df.sort_values('time').reset_index(drop=True)
    
    ict_canonical = sorted(list(set(s.replace('micro', '') for s in PRUNED_ASSET_UNIVERSE['ICT'])))
    df_enabled = df[df['symbol'].isin(ict_canonical)].reset_index(drop=True)
    
    # 1. Mediana móvil de riesgo (RiskExpansion)
    regime_ratios = []
    for i, row in df_enabled.iterrows():
        sym = row['symbol']
        past = df_enabled.iloc[:i]
        past_sym = past[past['symbol'] == sym]
        if len(past_sym) >= 5:
            baseline_risk = past_sym['risk_pct'].iloc[-20:].median()
            ratio = row['risk_pct'] / baseline_risk if baseline_risk > 0 else 1.0
        else:
            ratio = 1.0
        regime_ratios.append(ratio)
        
    df_enabled['risk_expansion_ratio'] = regime_ratios
    
    # 2. Contexto de persistencia H1/H4:
    # Si un trade ocurre en la misma dirección que la tendencia dominante de los últimos 5 trades del activo
    directional_alignment = []
    for i, row in df_enabled.iterrows():
        sym = row['symbol']
        past = df_enabled.iloc[:i]
        past_sym = past[past['symbol'] == sym]
        if len(past_sym) >= 3:
            # Racha reciente de dirección o ganancia
            last_dirs = past_sym['direction'].iloc[-3:].tolist()
            # Si al menos 2 de las últimas 3 fueron en la misma dirección
            same_dir_count = last_dirs.count(row['direction'])
            aligned = same_dir_count >= 2
        else:
            aligned = True
        directional_alignment.append(aligned)
        
    df_enabled['htf_momentum_aligned'] = directional_alignment
    
    # Split OOS 40%
    split_idx = int(len(df_enabled) * 0.60)
    test_df = df_enabled.iloc[split_idx:].copy().reset_index(drop=True)
    
    print("\nResultados en Holdout OOS (N=244):")
    # Base
    m_base = compute_metrics(test_df['rr'])
    print(f"  Base OOS: N={m_base['trades']} | Net R={m_base['net_r']:+.2f}R | Exp={m_base['exp_r']:+.4f}R | PF={m_base['pf']:.3f} | MaxDD={m_base['max_dd_r']:.2f}R")
    
    # Excl Jump 25 + Body Ratio
    f_def = (~test_df['symbol'].isin(['Jump 25 Index'])) & (test_df['body_ratio'] > 0.50)
    m_def = compute_metrics(test_df[f_def]['rr'])
    print(f"  Defensivo (Excl Jump25 + BodyRatio): N={m_def['trades']} | Net R={m_def['net_r']:+.2f}R | Exp={m_def['exp_r']:+.4f}R | PF={m_def['pf']:.3f} | MaxDD={m_def['max_dd_r']:.2f}R")
    
    # Defensivo + RiskExpansion <= 1.40
    f_reg = f_def & (test_df['risk_expansion_ratio'] <= 1.40)
    m_reg = compute_metrics(test_df[f_reg]['rr'])
    print(f"  Defensivo + RiskExpansion <= 1.40: N={m_reg['trades']} | Net R={m_reg['net_r']:+.2f}R | Exp={m_reg['exp_r']:+.4f}R | PF={m_reg['pf']:.3f} | MaxDD={m_reg['max_dd_r']:.2f}R")
    
    # Defensivo + RiskExpansion <= 1.40 + HTF Momentum Aligned
    f_htf = f_reg & test_df['htf_momentum_aligned']
    m_htf = compute_metrics(test_df[f_htf]['rr'])
    print(f"  Defensivo + RiskExpansion + HTF Momentum: N={m_htf['trades']} | Net R={m_htf['net_r']:+.2f}R | Exp={m_htf['exp_r']:+.4f}R | PF={m_htf['pf']:.3f} | MaxDD={m_htf['max_dd_r']:.2f}R")

if __name__ == "__main__":
    audit_snr_individual_assets()
    audit_ict_htf_and_regime()
