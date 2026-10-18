"""
scratch/comprehensive_walk_forward_and_hypotheses.py
===================================================
Script de investigación aislada para validación walk-forward anidada,
ablaciones de hipótesis, análisis de costos y consistencia multiactivo
conforme a los requerimientos del plan de auditoría.
"""

import sys
from pathlib import Path
import json
import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import brier_score_loss

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Configuración de codificación para consola
for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

from config.strategy_config import PRUNED_ASSET_UNIVERSE
from strategy.malaysian_snr.config import MalaysianSNRConfig

def compute_metrics(rr_series: pd.Series) -> dict:
    if len(rr_series) == 0:
        return {"trades": 0, "wr": 0.0, "net_r": 0.0, "exp_r": 0.0, "pf": 0.0, "max_dd_r": 0.0}
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
        "max_dd_r": round(max_dd, 2)
    }

def bootstrap_ci(rr_series: pd.Series, n_boot: int = 1000, ci: float = 0.95):
    if len(rr_series) < 5:
        return {"mean_ci": (0.0, 0.0), "pf_ci": (0.0, 0.0)}
    arr = rr_series.values
    means = []
    pfs = []
    np.random.seed(42)
    for _ in range(n_boot):
        sample = np.random.choice(arr, size=len(arr), replace=True)
        means.append(np.mean(sample))
        w = sample[sample > 0]
        l = sample[sample <= 0]
        g = np.sum(w) if len(w) > 0 else 0.0
        ls = np.abs(np.sum(l)) if len(l) > 0 else 0.0
        pfs.append(g / ls if ls > 0 else 99.0)
    
    alpha = (1.0 - ci) / 2.0
    mean_ci = (round(np.percentile(means, alpha * 100), 4), round(np.percentile(means, (1.0 - alpha) * 100), 4))
    pf_ci = (round(np.percentile(pfs, alpha * 100), 3), round(np.percentile(pfs, (1.0 - alpha) * 100), 3))
    return {"mean_ci": mean_ci, "pf_ci": pf_ci}

def main():
    print("=" * 80)
    print("AUDITORÍA FORENSE EXPERIMENTAL Y VALIDACIÓN WALK-FORWARD ICT Y MSNR")
    print("=" * 80)

    # 1. UNIVERSOS Y ACTIVOS HABILITADOS
    ict_canonical = sorted(list(set(s.replace('micro', '') for s in PRUNED_ASSET_UNIVERSE['ICT'])))
    msnr_allowed = MalaysianSNRConfig.allowed_symbols

    print(f"\n1. UNIVERSOS VIGENTES EN CONFIGURACIÓN:")
    print(f"  - ICT: {len(ict_canonical)} activos canónicos:")
    print(f"    {ict_canonical}")
    print(f"  - Malaysian SNR: {len(msnr_allowed)} activos en allowed_symbols:")
    print(f"    {msnr_allowed}")

    # 2. CARGA DE DATOS FAITHFUL
    df_ict = pd.read_csv(PROJECT_ROOT / "storage" / "analysis" / "ict_faithful_trades.csv")
    df_ict['time'] = pd.to_datetime(df_ict['time'], utc=True)
    df_ict = df_ict.sort_values('time').reset_index(drop=True)
    df_ict['exit_time'] = df_ict['time'] + pd.to_timedelta(df_ict['bars'] * 5, unit='m')
    df_ict_en = df_ict[df_ict['symbol'].isin(ict_canonical)].reset_index(drop=True)

    df_msnr = pd.read_csv(PROJECT_ROOT / "storage" / "analysis" / "msnr_faithful_trades.csv")
    df_msnr['time'] = pd.to_datetime(df_msnr['time'], utc=True)
    df_msnr = df_msnr.sort_values('time').reset_index(drop=True)
    df_msnr['exit_time'] = df_msnr['time'] + pd.to_timedelta(df_msnr['bars'] * 15, unit='m')
    df_msnr_en = df_msnr[df_msnr['symbol'].isin(msnr_allowed)].reset_index(drop=True)

    # Activos sin trades
    ict_no_trades = [s for s in ict_canonical if s not in df_ict_en['symbol'].unique()]
    msnr_no_trades = [s for s in msnr_allowed if s not in df_msnr_en['symbol'].unique()]
    print(f"\n  - Activos ICT sin trades en el dataset ({len(ict_no_trades)}): {ict_no_trades}")
    print(f"  - Activos SNR sin trades en el dataset ({len(msnr_no_trades)}): {msnr_no_trades}")

    # 3. ICT WALK-FORWARD MULTI-VENTANA (3 VENTANAS TEMPORALES INDEPENDIENTES)
    print("\n" + "=" * 80)
    print("2. ICT: VALIDACIÓN WALK-FORWARD EN 3 VENTANAS TEMPORALES INDEPENDIENTES")
    print("=" * 80)
    
    # Dividir el año de ICT en 3 ventanas temporales de ~4 meses
    t_min_ict = df_ict_en['time'].min()
    t_max_ict = df_ict_en['time'].max()
    t_range_ict = (t_max_ict - t_min_ict) / 3
    
    w1_end_ict = t_min_ict + t_range_ict
    w2_end_ict = w1_end_ict + t_range_ict
    
    print(f"Rango total ICT: {t_min_ict.date()} a {t_max_ict.date()} (N={len(df_ict_en)})")
    print(f"  Ventana 1: {t_min_ict.date()} a {w1_end_ict.date()}")
    print(f"  Ventana 2: {w1_end_ict.date()} a {w2_end_ict.date()}")
    print(f"  Ventana 3: {w2_end_ict.date()} a {t_max_ict.date()}")

    ict_w1 = df_ict_en[(df_ict_en['time'] >= t_min_ict) & (df_ict_en['time'] < w1_end_ict)].copy()
    ict_w2 = df_ict_en[(df_ict_en['time'] >= w1_end_ict) & (df_ict_en['time'] < w2_end_ict)].copy()
    ict_w3 = df_ict_en[(df_ict_en['time'] >= w2_end_ict) & (df_ict_en['time'] <= t_max_ict)].copy()

    # Función para aplicar filtros de ICT
    def apply_ict_filters(df_sub, exclude_premarket=True, exclude_dead=True, exclude_j25=True, body_gt_50=True):
        m = pd.Series(True, index=df_sub.index)
        if exclude_premarket:
            m = m & (~df_sub['ny_hour'].isin([7, 8]))
        if exclude_dead:
            m = m & (~df_sub['ny_hour'].isin([0, 6, 20, 22]))
        if exclude_j25:
            m = m & (~df_sub['symbol'].isin(['Jump 25 Index']))
        if body_gt_50:
            m = m & (df_sub['body_ratio'] > 0.50)
        return df_sub[m]

    # Evaluación por ventana (Filtros Reportados)
    for name, w_df in [("Ventana 1", ict_w1), ("Ventana 2", ict_w2), ("Ventana 3", ict_w3)]:
        m_base = compute_metrics(w_df['rr'])
        w_filt = apply_ict_filters(w_df)
        m_filt = compute_metrics(w_filt['rr'])
        print(f"  {name} ({len(w_df)} base trades):")
        print(f"    - Base: N={m_base['trades']} | Net R={m_base['net_r']}R | PF={m_base['pf']} | MaxDD={m_base['max_dd_r']}R")
        print(f"    - Filtros Reportados: N={m_filt['trades']} | Net R={m_filt['net_r']}R | PF={m_filt['pf']} | MaxDD={m_filt['max_dd_r']}R")

    # Walk-Forward Anidado Genuino (Train en W1 -> Test en W2; Train en W1+W2 -> Test en W3)
    print("\n  >>> WALK-FORWARD ESTRICTAMENTE ANIDADO (SIN LOOKAHEAD) ICT:")
    # Paso 1: Train en W1, Test en W2
    train1_pnl_hours = ict_w1.groupby('ny_hour')['rr'].sum()
    train1_bad_hours = set(train1_pnl_hours[train1_pnl_hours < 0].index)
    train1_bad_assets = set(ict_w1.groupby('symbol')['rr'].sum()[lambda x: x < 0].index)
    
    test_w2_nested = ict_w2[(~ict_w2['ny_hour'].isin(train1_bad_hours)) & 
                            (~ict_w2['symbol'].isin(train1_bad_assets)) & 
                            (ict_w2['body_ratio'] > 0.50)]
    m_test_w2_nested = compute_metrics(test_w2_nested['rr'])
    print(f"    Paso 1 (Train W1 -> Test OOS W2):")
    print(f"      Reglas descubiertas en W1: Horas excluidas={sorted(list(train1_bad_hours))}, Activos={sorted(list(train1_bad_assets))}")
    print(f"      Resultado en W2 OOS: N={m_test_w2_nested['trades']} | Net R={m_test_w2_nested['net_r']}R | PF={m_test_w2_nested['pf']} | MaxDD={m_test_w2_nested['max_dd_r']}R")

    # Paso 2: Train en W1+W2, Test en W3
    train12 = pd.concat([ict_w1, ict_w2])
    train12_pnl_hours = train12.groupby('ny_hour')['rr'].sum()
    train12_bad_hours = set(train12_pnl_hours[train12_pnl_hours < 0].index)
    train12_bad_assets = set(train12.groupby('symbol')['rr'].sum()[lambda x: x < 0].index)
    
    test_w3_nested = ict_w3[(~ict_w3['ny_hour'].isin(train12_bad_hours)) & 
                            (~ict_w3['symbol'].isin(train12_bad_assets)) & 
                            (ict_w3['body_ratio'] > 0.50)]
    m_test_w3_nested = compute_metrics(test_w3_nested['rr'])
    print(f"    Paso 2 (Train W1+W2 -> Test OOS W3):")
    print(f"      Reglas descubiertas en W1+W2: Horas excluidas={sorted(list(train12_bad_hours))}, Activos={sorted(list(train12_bad_assets))}")
    print(f"      Resultado en W3 OOS: N={m_test_w3_nested['trades']} | Net R={m_test_w3_nested['net_r']}R | PF={m_test_w3_nested['pf']} | MaxDD={m_test_w3_nested['max_dd_r']}R")

    # 4. MALAYSIAN SNR WALK-FORWARD MULTI-VENTANA (3 VENTANAS TEMPORALES INDEPENDIENTES)
    print("\n" + "=" * 80)
    print("3. MALAYSIAN SNR: VALIDACIÓN WALK-FORWARD EN 3 VENTANAS TEMPORALES INDEPENDIENTES")
    print("=" * 80)
    t_min_snr = df_msnr_en['time'].min()
    t_max_snr = df_msnr_en['time'].max()
    t_range_snr = (t_max_snr - t_min_snr) / 3
    
    w1_end_snr = t_min_snr + t_range_snr
    w2_end_snr = w1_end_snr + t_range_snr
    
    print(f"Rango total SNR: {t_min_snr.date()} a {t_max_snr.date()} (N={len(df_msnr_en)})")
    print(f"  Ventana 1: {t_min_snr.date()} a {w1_end_snr.date()}")
    print(f"  Ventana 2: {w1_end_snr.date()} a {w2_end_snr.date()}")
    print(f"  Ventana 3: {w2_end_snr.date()} a {t_max_snr.date()}")

    snr_w1 = df_msnr_en[(df_msnr_en['time'] >= t_min_snr) & (df_msnr_en['time'] < w1_end_snr)].copy()
    snr_w2 = df_msnr_en[(df_msnr_en['time'] >= w1_end_snr) & (df_msnr_en['time'] < w2_end_snr)].copy()
    snr_w3 = df_msnr_en[(df_msnr_en['time'] >= w2_end_snr) & (df_msnr_en['time'] <= t_max_snr)].copy()

    def apply_snr_filters(df_sub):
        return df_sub[(df_sub['scenario'] != 'ESC_1_CONTINUATION') & 
                      (~df_sub['symbol'].isin(['Jump 25 Index', 'USDJPY', 'XAGUSD'])) & 
                      (df_sub['body_ratio'] >= 0.50) & 
                      (df_sub['adx'] >= 20.0)]

    for name, w_df in [("Ventana 1", snr_w1), ("Ventana 2", snr_w2), ("Ventana 3", snr_w3)]:
        m_base = compute_metrics(w_df['rr'])
        w_filt = apply_snr_filters(w_df)
        m_filt = compute_metrics(w_filt['rr'])
        print(f"  {name} ({len(w_df)} base trades):")
        print(f"    - Base: N={m_base['trades']} | Net R={m_base['net_r']}R | PF={m_base['pf']} | MaxDD={m_base['max_dd_r']}R")
        print(f"    - Filtros Reportados: N={m_filt['trades']} | Net R={m_filt['net_r']}R | PF={m_filt['pf']} | MaxDD={m_filt['max_dd_r']}R")

    print("\n  >>> WALK-FORWARD ESTRICTAMENTE ANIDADO (SIN LOOKAHEAD) MALAYSIAN SNR:")
    # Paso 1: Train en W1 -> Test en W2
    train1_snr_bad_scenarios = set(snr_w1.groupby('scenario')['rr'].sum()[lambda x: x < 0].index)
    train1_snr_bad_assets = set(snr_w1.groupby('symbol')['rr'].sum()[lambda x: x < 0].index)
    test_snr_w2_nested = snr_w2[(~snr_w2['scenario'].isin(train1_snr_bad_scenarios)) & 
                                (~snr_w2['symbol'].isin(train1_snr_bad_assets)) & 
                                (snr_w2['body_ratio'] >= 0.50) & 
                                (snr_w2['adx'] >= 20.0)]
    m_test_snr_w2_nested = compute_metrics(test_snr_w2_nested['rr'])
    print(f"    Paso 1 (Train W1 -> Test OOS W2):")
    print(f"      Reglas descubiertas en W1: Escenarios excluidos={sorted(list(train1_snr_bad_scenarios))}, Activos={sorted(list(train1_snr_bad_assets))}")
    print(f"      Resultado en W2 OOS: N={m_test_snr_w2_nested['trades']} | Net R={m_test_snr_w2_nested['net_r']}R | PF={m_test_snr_w2_nested['pf']} | MaxDD={m_test_snr_w2_nested['max_dd_r']}R")

    # Paso 2: Train en W1+W2 -> Test en W3
    train12_snr = pd.concat([snr_w1, snr_w2])
    train12_snr_bad_scenarios = set(train12_snr.groupby('scenario')['rr'].sum()[lambda x: x < 0].index)
    train12_snr_bad_assets = set(train12_snr.groupby('symbol')['rr'].sum()[lambda x: x < 0].index)
    test_snr_w3_nested = snr_w3[(~snr_w3['scenario'].isin(train12_snr_bad_scenarios)) & 
                                (~snr_w3['symbol'].isin(train12_snr_bad_assets)) & 
                                (snr_w3['body_ratio'] >= 0.50) & 
                                (snr_w3['adx'] >= 20.0)]
    m_test_snr_w3_nested = compute_metrics(test_snr_w3_nested['rr'])
    print(f"    Paso 2 (Train W1+W2 -> Test OOS W3):")
    print(f"      Reglas descubiertas en W1+W2: Escenarios excluidos={sorted(list(train12_snr_bad_scenarios))}, Activos={sorted(list(train12_snr_bad_assets))}")
    print(f"      Resultado en W3 OOS: N={m_test_snr_w3_nested['trades']} | Net R={m_test_snr_w3_nested['net_r']}R | PF={m_test_snr_w3_nested['pf']} | MaxDD={m_test_snr_w3_nested['max_dd_r']}R")

    # 5. DETALLE DE ACTIVOS EN HOLDOUT
    print("\n" + "=" * 80)
    print("4. DETALLE ACTIVO POR ACTIVO EN HOLDOUT (40% FINAL)")
    print("=" * 80)
    
    # ICT Holdout
    split_ict = int(len(df_ict_en) * 0.6)
    test_ict = df_ict_en.iloc[split_ict:].copy()
    filt_ict_test = apply_ict_filters(test_ict)
    pnl_ict_test_base = test_ict.groupby('symbol')['rr'].sum()
    pnl_ict_test_filt = filt_ict_test.groupby('symbol')['rr'].sum()
    
    print("ICT HOLDOUT (15 SÍMBOLOS HABILITADOS):")
    pos_ict_h = 0
    for s in ict_canonical:
        nb = len(test_ict[test_ict['symbol'] == s])
        nf = len(filt_ict_test[filt_ict_test['symbol'] == s])
        rb = pnl_ict_test_base.get(s, 0.0)
        rf = pnl_ict_test_filt.get(s, 0.0)
        if rf > 0:
            pos_ict_h += 1
        print(f"  {s:<20} | Base: N={nb:3d}, Net R={rb:6.2f}R | Filtros: N={nf:3d}, Net R={rf:6.2f}R")
    print(f"  --> Positivos ICT Holdout Filtros: {pos_ict_h} / {len(ict_canonical)} ({pos_ict_h / len(ict_canonical) * 100:.1f}%)")

    # SNR Holdout
    split_snr = int(len(df_msnr_en) * 0.6)
    test_snr = df_msnr_en.iloc[split_snr:].copy()
    filt_snr_test = apply_snr_filters(test_snr)
    pnl_snr_test_base = test_snr.groupby('symbol')['rr'].sum()
    pnl_snr_test_filt = filt_snr_test.groupby('symbol')['rr'].sum()
    
    print("\nMALAYSIAN SNR HOLDOUT (23 SÍMBOLOS HABILITADOS):")
    pos_snr_h = 0
    for s in msnr_allowed:
        nb = len(test_snr[test_snr['symbol'] == s])
        nf = len(filt_snr_test[filt_snr_test['symbol'] == s])
        rb = pnl_snr_test_base.get(s, 0.0)
        rf = pnl_snr_test_filt.get(s, 0.0)
        if rf > 0:
            pos_snr_h += 1
        print(f"  {s:<20} | Base: N={nb:3d}, Net R={rb:6.2f}R | Filtros: N={nf:3d}, Net R={rf:6.2f}R")
    print(f"  --> Positivos SNR Holdout Filtros: {pos_snr_h} / {len(msnr_allowed)} ({pos_snr_h / len(msnr_allowed) * 100:.1f}%)")

    # 6. SENSIBILIDAD A COSTOS (SPREAD ADICIONAL, SLIPPAGE, GAP SL)
    print("\n" + "=" * 80)
    print("5. ANÁLISIS DE SENSIBILIDAD A COSTOS Y ESTRÉS EN HOLDOUT")
    print("=" * 80)

    def stress_costs(rr_series, slippage_r=0.0, gap_sl_factor=1.0):
        adj_rr = []
        for r in rr_series:
            if r <= 0:
                adj_rr.append((r * gap_sl_factor) - slippage_r)
            else:
                adj_rr.append(r - slippage_r)
        return pd.Series(adj_rr)

    print("ICT Holdout Filtros Reportados:")
    for slip, gap in [(0.0, 1.0), (0.05, 1.0), (0.10, 1.0), (0.05, 1.15), (0.10, 1.15)]:
        s_rr = stress_costs(filt_ict_test['rr'], slippage_r=slip, gap_sl_factor=gap)
        m = compute_metrics(s_rr)
        print(f"  - Deslizamiento {slip:.2f}R, Gap SL Factor {gap:.2f}: Net R={m['net_r']}R | PF={m['pf']} | MaxDD={m['max_dd_r']}R")

    print("\nMalaysian SNR Holdout Filtros Reportados:")
    for slip, gap in [(0.0, 1.0), (0.05, 1.0), (0.10, 1.0), (0.05, 1.15), (0.10, 1.15)]:
        s_rr = stress_costs(filt_snr_test['rr'], slippage_r=slip, gap_sl_factor=gap)
        m = compute_metrics(s_rr)
        print(f"  - Deslizamiento {slip:.2f}R, Gap SL Factor {gap:.2f}: Net R={m['net_r']}R | PF={m['pf']} | MaxDD={m['max_dd_r']}R")

if __name__ == "__main__":
    main()
