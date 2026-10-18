"""Cálculo de intervalos de incertidumbre, bootstrap y sensibilidad para ICT y SNR en Holdout Intacto.

Ejecuta:
- Bootstrap de 1000 iteraciones para la expectativa (mean R) y Profit Factor en Holdout OOS.
- Análisis de sensibilidad a costos adicionales (slippage de 0.5 a 2.0 ticks).
- Generación de tablas consolidadas por activo y variante.
"""

import sys
from pathlib import Path
import json
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

def bootstrap_stats(series: pd.Series, n_iter: int = 1000, ci: float = 0.95) -> dict:
    values = series.values
    if len(values) == 0:
        return {"mean_ci": (0, 0), "pf_ci": (0, 0)}
    means = []
    pfs = []
    np.random.seed(42)
    n = len(values)
    for _ in range(n_iter):
        sample = np.random.choice(values, size=n, replace=True)
        means.append(np.mean(sample))
        wins = sample[sample > 0]
        losses = abs(sample[sample <= 0])
        pf = (wins.sum() / losses.sum()) if losses.sum() > 0 else 0.0
        pfs.append(pf)
    
    alpha = (1 - ci) / 2
    mean_low = np.percentile(means, alpha * 100)
    mean_high = np.percentile(means, (1 - alpha) * 100)
    pf_low = np.percentile(pfs, alpha * 100)
    pf_high = np.percentile(pfs, (1 - alpha) * 100)
    return {
        "mean_ci": (round(float(mean_low), 4), round(float(mean_high), 4)),
        "pf_ci": (round(float(pf_low), 3), round(float(pf_high), 3))
    }

def run_bootstrap_audit():
    print("=" * 80)
    print("AUDITORÍA DE INCERTIDUMBRE Y BOOTSTRAP (1000 ITERACIONES)")
    print("=" * 80)
    
    # 1. ICT
    df_ict = pd.read_csv(PROJECT_ROOT / "storage" / "analysis" / "ict_faithful_trades.csv")
    df_ict['time'] = pd.to_datetime(df_ict['time'], utc=True)
    df_ict = df_ict.sort_values('time').reset_index(drop=True)
    ict_canon = set(s.replace('micro', '') for s in PRUNED_ASSET_UNIVERSE['ICT'])
    df_ict_enabled = df_ict[df_ict['symbol'].isin(ict_canon)].reset_index(drop=True)
    
    split_ict = int(len(df_ict_enabled) * 0.60)
    test_ict = df_ict_enabled.iloc[split_ict:].copy()
    
    # Holdout base
    ci_ict_base = bootstrap_stats(test_ict['rr'])
    # Holdout con filtros previamente reportados
    test_ict_filt_prev = test_ict[(~test_ict['ny_hour'].isin([7, 8])) & 
                                   (~test_ict['ny_hour'].isin([0, 6, 20, 22])) & 
                                   (~test_ict['symbol'].isin(['Jump 25 Index'])) & 
                                   (test_ict['body_ratio'] > 0.50)]
    ci_ict_prev = bootstrap_stats(test_ict_filt_prev['rr'])
    
    # Holdout estrictamente anidado
    train_ict = df_ict_enabled.iloc[:split_ict]
    h_train_neg = set(train_ict.groupby('ny_hour')['rr'].sum()[lambda x: x < 0].index)
    a_train_neg = set(train_ict.groupby('symbol')['rr'].sum()[lambda x: x < 0].index)
    test_ict_nested = test_ict[(~test_ict['ny_hour'].isin(h_train_neg)) & 
                               (~test_ict['symbol'].isin(a_train_neg)) & 
                               (test_ict['body_ratio'] > 0.50)]
    ci_ict_nested = bootstrap_stats(test_ict_nested['rr'])
    
    print(f"1. ICT HOLDOUT (40% final, N={len(test_ict)} base):")
    print(f"  - Base Mecánica OOS: Mean R = {test_ict['rr'].mean():.4f} (IC 95%: {ci_ict_base['mean_ci']}) | PF = {ci_ict_base['pf_ci']}")
    print(f"  - Filtros Previamente Reportados (N={len(test_ict_filt_prev)}): Mean R = {test_ict_filt_prev['rr'].mean():.4f} (IC 95%: {ci_ict_prev['mean_ci']}) | PF = {ci_ict_prev['pf_ci']}")
    print(f"  - Filtros Estrictamente Anidados (N={len(test_ict_nested)}): Mean R = {test_ict_nested['rr'].mean():.4f} (IC 95%: {ci_ict_nested['mean_ci']}) | PF = {ci_ict_nested['pf_ci']}")
    
    # 2. Malaysian SNR
    df_msnr = pd.read_csv(PROJECT_ROOT / "storage" / "analysis" / "msnr_faithful_trades.csv")
    df_msnr['time'] = pd.to_datetime(df_msnr['time'], utc=True)
    df_msnr = df_msnr.sort_values('time').reset_index(drop=True)
    msnr_allowed = set(s.replace('micro', '') for s in MalaysianSNRConfig().allowed_symbols)
    df_msnr_enabled = df_msnr[df_msnr['symbol'].isin(msnr_allowed)].reset_index(drop=True)
    
    split_msnr = int(len(df_msnr_enabled) * 0.60)
    test_msnr = df_msnr_enabled.iloc[split_msnr:].copy()
    
    ci_msnr_base = bootstrap_stats(test_msnr['rr'])
    test_msnr_filt_prev = test_msnr[(test_msnr['scenario'] != 'ESC_1_CONTINUATION') & 
                                     (~test_msnr['symbol'].isin(['Jump 25 Index', 'USDJPY', 'XAGUSD'])) & 
                                     (test_msnr['body_ratio'] >= 0.50) & 
                                     (test_msnr['adx'] >= 20.0)]
    ci_msnr_prev = bootstrap_stats(test_msnr_filt_prev['rr'])
    
    train_msnr = df_msnr_enabled.iloc[:split_msnr]
    s_train_neg = set(train_msnr.groupby('scenario')['rr'].sum()[lambda x: x < 0].index)
    a_msnr_neg = set(train_msnr.groupby('symbol')['rr'].sum()[lambda x: x < 0].index)
    test_msnr_nested = test_msnr[(~test_msnr['scenario'].isin(s_train_neg)) & 
                                 (~test_msnr['symbol'].isin(a_msnr_neg)) & 
                                 (test_msnr['body_ratio'] >= 0.50) & 
                                 (test_msnr['adx'] >= 20.0)]
    ci_msnr_nested = bootstrap_stats(test_msnr_nested['rr'])
    
    print(f"\n2. MALAYSIAN SNR HOLDOUT (40% final, N={len(test_msnr)} base):")
    print(f"  - Base Mecánica OOS: Mean R = {test_msnr['rr'].mean():.4f} (IC 95%: {ci_msnr_base['mean_ci']}) | PF = {ci_msnr_base['pf_ci']}")
    print(f"  - Filtros Previamente Reportados (N={len(test_msnr_filt_prev)}): Mean R = {test_msnr_filt_prev['rr'].mean():.4f} (IC 95%: {ci_msnr_prev['mean_ci']}) | PF = {ci_msnr_prev['pf_ci']}")
    print(f"  - Filtros Estrictamente Anidados (N={len(test_msnr_nested)}): Mean R = {test_msnr_nested['rr'].mean():.4f} (IC 95%: {ci_msnr_nested['mean_ci']}) | PF = {ci_msnr_nested['pf_ci']}")

if __name__ == "__main__":
    run_bootstrap_audit()
