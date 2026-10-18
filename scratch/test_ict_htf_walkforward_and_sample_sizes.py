"""Validación walk-forward independiente de ICT (RiskExpansion + HTF Momentum),
comprobación estricta de causalidad ex-ante y análisis de tamaño muestral en SNR.
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

def test_ict_htf_momentum_walkforward():
    print("=" * 80)
    print("VALIDACIÓN WALK-FORWARD DE ICT: DEFENSIVO + RISK EXPANSION + HTF MOMENTUM")
    print("=" * 80)
    
    df = pd.read_csv(PROJECT_ROOT / "storage" / "analysis" / "ict_faithful_trades.csv")
    df['time'] = pd.to_datetime(df['time'], utc=True)
    df = df.sort_values('time').reset_index(drop=True)
    df['exit_time'] = df['time'] + pd.to_timedelta(df['bars'] * 5, unit='m')
    
    ict_canonical = sorted(list(set(s.replace('micro', '') for s in PRUNED_ASSET_UNIVERSE['ICT'])))
    df_enabled = df[df['symbol'].isin(ict_canonical)].reset_index(drop=True)
    
    # 1. Variables estrictamente causales ex-ante (disponibles en t < open_time)
    regime_ratios = []
    directional_alignment = []
    
    for i, row in df_enabled.iterrows():
        sym = row['symbol']
        past = df_enabled.iloc[:i]
        past_sym = past[past['symbol'] == sym]
        
        # Risk expansion: mediana de los últimos 20 trades estrictamente previos
        if len(past_sym) >= 5:
            baseline_risk = past_sym['risk_pct'].iloc[-20:].median()
            ratio = row['risk_pct'] / baseline_risk if baseline_risk > 0 else 1.0
        else:
            ratio = 1.0
        regime_ratios.append(ratio)
        
        # HTF Momentum alignment: dirección de las últimas 3 entradas previas
        if len(past_sym) >= 3:
            last_dirs = past_sym['direction'].iloc[-3:].tolist()
            aligned = last_dirs.count(row['direction']) >= 2
        else:
            aligned = True
        directional_alignment.append(aligned)
        
    df_enabled['risk_expansion_ratio'] = regime_ratios
    df_enabled['htf_momentum_aligned'] = directional_alignment
    
    # Timeline
    min_time = df_enabled['time'].min()
    max_time = df_enabled['time'].max()
    total_days = (max_time - min_time).days
    
    w1_end = min_time + pd.Timedelta(days=int(total_days * 0.333))
    w2_end = min_time + pd.Timedelta(days=int(total_days * 0.666))
    
    w1_trades = df_enabled[df_enabled['time'] < w1_end].copy()
    w2_trades = df_enabled[(df_enabled['time'] >= w1_end) & (df_enabled['time'] < w2_end)].copy()
    w3_trades = df_enabled[df_enabled['time'] >= w2_end].copy()
    
    w1_clean = w1_trades[w1_trades['exit_time'] < w1_end].copy()
    w2_clean = w2_trades[w2_trades['exit_time'] < w2_end].copy()
    
    print(f"Ventana 1 (Train inicial): {len(w1_clean)} trades | Ventana 2 (OOS 1): {len(w2_clean)} trades | Ventana 3 (OOS 2): {len(w3_trades)} trades")
    
    def eval_subset(data_df):
        m_base = compute_metrics(data_df['rr'])
        
        f_def = (~data_df['symbol'].isin(['Jump 25 Index'])) & (data_df['body_ratio'] > 0.50)
        m_def = compute_metrics(data_df[f_def]['rr'])
        
        f_reg = f_def & (data_df['risk_expansion_ratio'] <= 1.40)
        m_reg = compute_metrics(data_df[f_reg]['rr'])
        
        f_htf = f_reg & data_df['htf_momentum_aligned']
        m_htf = compute_metrics(data_df[f_htf]['rr'])
        
        return m_base, m_def, m_reg, m_htf

    print("\n" + "-" * 80)
    print("PASO 1 WALK-FORWARD: Prueba en Ventana 2 OOS")
    print("-" * 80)
    b2, d2, r2, h2 = eval_subset(w2_clean)
    print(f"  Base Mecánica                         : N={b2['trades']:3d} | Net R={b2['net_r']:+6.2f}R | Exp={b2['exp_r']:+7.4f}R | PF={b2['pf']:5.3f} | MaxDD={b2['max_dd_r']:5.2f}R")
    print(f"  Defensivo (Excl Jump25 + BodyRatio)   : N={d2['trades']:3d} | Net R={d2['net_r']:+6.2f}R | Exp={d2['exp_r']:+7.4f}R | PF={d2['pf']:5.3f} | MaxDD={d2['max_dd_r']:5.2f}R")
    print(f"  Defensivo + RiskExpansion <= 1.40     : N={r2['trades']:3d} | Net R={r2['net_r']:+6.2f}R | Exp={r2['exp_r']:+7.4f}R | PF={r2['pf']:5.3f} | MaxDD={r2['max_dd_r']:5.2f}R")
    print(f"  Defensivo + RiskExpansion + HTF Mom   : N={h2['trades']:3d} | Net R={h2['net_r']:+6.2f}R | Exp={h2['exp_r']:+7.4f}R | PF={h2['pf']:5.3f} | MaxDD={h2['max_dd_r']:5.2f}R")
    
    print("\n" + "-" * 80)
    print("PASO 2 WALK-FORWARD: Prueba en Ventana 3 OOS (Holdout Final)")
    print("-" * 80)
    b3, d3, r3, h3 = eval_subset(w3_trades)
    print(f"  Base Mecánica                         : N={b3['trades']:3d} | Net R={b3['net_r']:+6.2f}R | Exp={b3['exp_r']:+7.4f}R | PF={b3['pf']:5.3f} | MaxDD={b3['max_dd_r']:5.2f}R")
    print(f"  Defensivo (Excl Jump25 + BodyRatio)   : N={d3['trades']:3d} | Net R={d3['net_r']:+6.2f}R | Exp={d3['exp_r']:+7.4f}R | PF={d3['pf']:5.3f} | MaxDD={d3['max_dd_r']:5.2f}R")
    print(f"  Defensivo + RiskExpansion <= 1.40     : N={r3['trades']:3d} | Net R={r3['net_r']:+6.2f}R | Exp={r3['exp_r']:+7.4f}R | PF={r3['pf']:5.3f} | MaxDD={r3['max_dd_r']:5.2f}R")
    print(f"  Defensivo + RiskExpansion + HTF Mom   : N={h3['trades']:3d} | Net R={h3['net_r']:+6.2f}R | Exp={h3['exp_r']:+7.4f}R | PF={h3['pf']:5.3f} | MaxDD={h3['max_dd_r']:5.2f}R")

def audit_sample_sizes_and_missing_assets():
    print("\n" + "=" * 80)
    print("AUDITORÍA DE TAMAÑO MUESTRAL EN SNR Y COBERTURA FALTANTE DE ACTIVOS")
    print("=" * 80)
    
    # 1. SNR sample sizes
    df_snr = pd.read_csv(PROJECT_ROOT / "storage" / "analysis" / "msnr_faithful_trades.csv")
    msnr_cfg = MalaysianSNRConfig()
    snr_allowed = sorted(list(set(s.replace('micro', '') for s in msnr_cfg.allowed_symbols)))
    snr_observed = sorted(df_snr['symbol'].unique().tolist())
    snr_missing = sorted(list(set(snr_allowed) - set(snr_observed)))
    
    print(f"Malaysian SNR: Universo configurado = {len(snr_allowed)} | Observados con trades = {len(snr_observed)} | Cobertura pendiente = {len(snr_missing)}")
    print("  14 Activos SNR sin evidencia / cobertura pendiente:")
    for i in range(0, len(snr_missing), 3):
        print("    " + ", ".join(snr_missing[i:i+3]))
        
    # 2. ICT sample sizes
    df_ict = pd.read_csv(PROJECT_ROOT / "storage" / "analysis" / "ict_faithful_trades.csv")
    ict_canonical = sorted(list(set(s.replace('micro', '') for s in PRUNED_ASSET_UNIVERSE['ICT'])))
    ict_observed = sorted(df_ict['symbol'].unique().tolist())
    ict_missing = sorted(list(set(ict_canonical) - set(ict_observed)))
    
    print(f"\nICT Sabri Malle: Universo canónico = {len(ict_canonical)} | Observados con trades = {len(ict_observed)} | Cobertura pendiente = {len(ict_missing)}")
    print("  4 Activos ICT sin evidencia / cobertura pendiente:")
    print("    " + ", ".join(ict_missing))

if __name__ == "__main__":
    test_ict_htf_momentum_walkforward()
    audit_sample_sizes_and_missing_assets()
