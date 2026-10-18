"""
scratch/comprehensive_snr_esc1_and_causal_audit.py
==================================================
Auditoría causal exhaustiva, reconciliación de Escenario 1 en Malaysian SNR,
pruebas de ablación en ICT, validación walk-forward anidada y análisis de costos.
"""

import sys
from pathlib import Path
import json
import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression

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

def stress_costs(rr_series: pd.Series, slippage_r: float = 0.0, gap_sl_factor: float = 1.0) -> pd.Series:
    adj = []
    for r in rr_series:
        if r <= 0:
            adj.append((r * gap_sl_factor) - slippage_r)
        else:
            adj.append(r - slippage_r)
    return pd.Series(adj)

def main():
    print("=" * 80)
    print("AUDITORÍA FORENSE EXPERIMENTAL: RECONCILIACIÓN DEL ESCENARIO 1 Y VALIDACIÓN CAUSAL")
    print("=" * 80)

    # 1. CARGA Y RECONCILIACIÓN DE DATOS MALAYSIAN SNR
    df_msnr_raw = pd.read_csv(PROJECT_ROOT / "storage" / "analysis" / "msnr_faithful_trades.csv")
    msnr_allowed = MalaysianSNRConfig.allowed_symbols
    df_msnr_raw['time'] = pd.to_datetime(df_msnr_raw['time'], utc=True)
    df_msnr_raw['exit_time'] = df_msnr_raw['time'] + pd.to_timedelta(df_msnr_raw['bars'] * 15, unit='m')
    
    # Filtrado estricto a los 23 símbolos de allowed_symbols
    df_snr = df_msnr_raw[df_msnr_raw['symbol'].isin(msnr_allowed)].copy()
    df_snr_sorted = df_snr.sort_values('time').reset_index(drop=True)
    
    print(f"1. UNIVERSO MALAYSIAN SNR ({len(msnr_allowed)} ACTIVOS HABILITADOS EN ALLOWED_SYMBOLS):")
    print(f"  - Filas totales en msnr_faithful_trades.csv: {len(df_msnr_raw)}")
    print(f"  - Filas sobre universo habilitado (23 símbolos): {len(df_snr)}")
    active_syms = df_snr['symbol'].unique().tolist()
    missing_syms = [s for s in msnr_allowed if s not in active_syms]
    print(f"  - Activos con operaciones ({len(active_syms)}): {active_syms}")
    print(f"  - Activos sin operaciones ({len(missing_syms)}): {missing_syms}")

    # Split 60/40 cronológico
    split_idx = int(len(df_snr_sorted) * 0.60)
    split_time = df_snr_sorted['time'].iloc[split_idx]
    train_snr = df_snr_sorted.iloc[:split_idx].copy()
    test_snr = df_snr_sorted.iloc[split_idx:].copy()
    train_snr_purged = train_snr[train_snr['exit_time'] < split_time].copy()

    print(f"\n2. PARTICIÓN TEMPORAL CRONOLÓGICA (60% TRAIN / 40% HOLDOUT OOS):")
    print(f"  - Train: {train_snr['time'].min() if not train_snr.empty else ''} a {train_snr['time'].max()} (N={len(train_snr)}, purgado N={len(train_snr_purged)})")
    print(f"  - Holdout OOS: {test_snr['time'].min()} a {test_snr['time'].max()} (N={len(test_snr)})")

    # 3. MATRIZ DE COMPARACIÓN DE ESCENARIO 1 EN IDÉNTICAS CONDICIONES
    print("\n" + "=" * 80)
    print("3. MALAYSIAN SNR: MATRIZ DE COMPARACIÓN DE ESCENARIO 1 (REPLAY Y HOLDOUT)")
    print("=" * 80)

    # Definición de filtros base
    mask_body_rep = df_snr_sorted['body_ratio'] >= 0.50
    mask_adx_rep = df_snr_sorted['adx'] >= 20.0
    mask_pruning_rep = ~df_snr_sorted['symbol'].isin(['Jump 25 Index', 'USDJPY', 'XAGUSD'])

    mask_body_test = test_snr['body_ratio'] >= 0.50
    mask_adx_test = test_snr['adx'] >= 20.0
    mask_pruning_test = ~test_snr['symbol'].isin(['Jump 25 Index', 'USDJPY', 'XAGUSD'])

    variants = [
        ("1. Mecánica Base (Todos los Escenarios)", 
         pd.Series(True, index=df_snr_sorted.index), 
         pd.Series(True, index=test_snr.index)),
        ("2. Escenario 1 Bloqueado Globalmente (Sin filtros)", 
         df_snr_sorted['scenario'] != 'ESC_1_CONTINUATION', 
         test_snr['scenario'] != 'ESC_1_CONTINUATION'),
        ("3. Escenario 1 Permitido Globalmente (Sin filtros)", 
         pd.Series(True, index=df_snr_sorted.index), 
         pd.Series(True, index=test_snr.index)),
        ("4. Solo Filtro Body Ratio >= 0.50 (Con Escenario 1)", 
         mask_body_rep, 
         mask_body_test),
        ("5. Solo Filtro Body Ratio >= 0.50 (Sin Escenario 1)", 
         mask_body_rep & (df_snr_sorted['scenario'] != 'ESC_1_CONTINUATION'), 
         mask_body_test & (test_snr['scenario'] != 'ESC_1_CONTINUATION')),
        ("6. Solo Filtro ADX >= 20.0 (Con Escenario 1)", 
         mask_adx_rep, 
         mask_adx_test),
        ("7. Solo Filtro ADX >= 20.0 (Sin Escenario 1)", 
         mask_adx_rep & (df_snr_sorted['scenario'] != 'ESC_1_CONTINUATION'), 
         mask_adx_test & (test_snr['scenario'] != 'ESC_1_CONTINUATION')),
        ("8. Filtros Body >= 0.50 & ADX >= 20.0 (Con Escenario 1)", 
         mask_body_rep & mask_adx_rep, 
         mask_body_test & mask_adx_test),
        ("9. Filtros Body >= 0.50 & ADX >= 20.0 (Sin Escenario 1)", 
         mask_body_rep & mask_adx_rep & (df_snr_sorted['scenario'] != 'ESC_1_CONTINUATION'), 
         mask_body_test & mask_adx_test & (test_snr['scenario'] != 'ESC_1_CONTINUATION')),
        ("10. Poda Activos + Body/ADX con Escenario 1 BLOQUEADO (Reportado Previo)", 
         mask_body_rep & mask_adx_rep & mask_pruning_rep & (df_snr_sorted['scenario'] != 'ESC_1_CONTINUATION'), 
         mask_body_test & mask_adx_test & mask_pruning_test & (test_snr['scenario'] != 'ESC_1_CONTINUATION')),
        ("11. Poda Activos + Body/ADX con Escenario 1 PERMITIDO (Variante +13.62 R)", 
         mask_body_rep & mask_adx_rep & mask_pruning_rep, 
         mask_body_test & mask_adx_test & mask_pruning_test),
    ]

    print(f"{'Variante':<62} | {'Replay N':<8} | {'Replay R':<10} | {'Replay PF':<9} | {'Holdout N':<9} | {'Holdout R':<10} | {'Holdout PF':<10} | {'MaxDD OOS'}")
    print("-" * 135)
    for name, m_rep, m_test in variants:
        res_rep = compute_metrics(df_snr_sorted[m_rep]['rr'])
        res_test = compute_metrics(test_snr[m_test]['rr'])
        print(f"{name:<62} | {res_rep['trades']:<8} | {res_rep['net_r']:<10.2f} | {res_rep['pf']:<9.3f} | {res_test['trades']:<9} | {res_test['net_r']:<10.2f} | {res_test['pf']:<10.3f} | {res_test['max_dd_r']:<8.2f}R")

    # 4. DECISIÓN DINÁMICA POR ACTIVO DE ESCENARIO 1 APRENDIDA EN TRAIN
    print("\n" + "=" * 80)
    print("4. MALAYSIAN SNR: ESCENARIO 1 APRENDIDO EXCLUSIVAMENTE EN ENTRENAMIENTO (POR ACTIVO)")
    print("=" * 80)
    
    # Análisis in-sample de Escenario 1 por activo en Train
    train_esc1 = train_snr_purged[train_snr_purged['scenario'] == 'ESC_1_CONTINUATION']
    train_esc1_by_sym = train_esc1.groupby('symbol')['rr'].agg(trades='count', net_r='sum')
    print("Rendimiento del Escenario 1 por activo en Train (In-Sample):")
    for s in active_syms:
        c = train_esc1_by_sym.loc[s, 'trades'] if s in train_esc1_by_sym.index else 0
        r = train_esc1_by_sym.loc[s, 'net_r'] if s in train_esc1_by_sym.index else 0.0
        print(f"  - {s:<20}: N={c:2d} | Net R = {r:6.2f}R")

    # Regla causal descubierta en Train: Bloquear Escenario 1 SOLO en activos donde Escenario 1 fue negativo en Train
    esc1_neg_in_train = set(train_esc1_by_sym[train_esc1_by_sym['net_r'] < 0].index)
    print(f"\nRegla aprendida en Train: Activos con Escenario 1 tóxico en Train ({len(esc1_neg_in_train)}): {esc1_neg_in_train}")
    
    # Aplicar al Holdout OOS:
    # Si el trade es Escenario 1 y el activo está en esc1_neg_in_train -> BLOQUEAR. De lo contrario, PERMITIR.
    mask_dynamic_esc1_holdout = ~( (test_snr['scenario'] == 'ESC_1_CONTINUATION') & (test_snr['symbol'].isin(esc1_neg_in_train)) )
    
    # Combinar con Body Ratio >= 0.50 y ADX >= 20.0
    test_dynamic_esc1 = test_snr[mask_dynamic_esc1_holdout & mask_body_test & mask_adx_test]
    res_dynamic = compute_metrics(test_dynamic_esc1['rr'])
    print(f"\nResultado en Holdout OOS con Escenario 1 dinámico por activo (sin poda previa):")
    print(f"  N = {res_dynamic['trades']} | Net R = {res_dynamic['net_r']:.2f}R | Exp = {res_dynamic['exp_r']:.4f}R | WR = {res_dynamic['wr']:.2f}% | PF = {res_dynamic['pf']:.3f} | MaxDD = {res_dynamic['max_dd_r']:.2f}R")

    # Si además se aplican activos positivos en Train:
    train_pnl_by_sym = train_snr_purged.groupby('symbol')['rr'].sum()
    train_pos_syms = set(train_pnl_by_sym[train_pnl_by_sym > 0].index)
    print(f"Activos netamente positivos en Train ({len(train_pos_syms)}): {train_pos_syms}")
    
    test_dynamic_nested = test_snr[test_snr['symbol'].isin(train_pos_syms) & mask_dynamic_esc1_holdout & mask_body_test & mask_adx_test]
    res_dynamic_nested = compute_metrics(test_dynamic_nested['rr'])
    print(f"\nResultado en Holdout OOS con Activos Positivos en Train + Escenario 1 dinámico + Body/ADX:")
    print(f"  N = {res_dynamic_nested['trades']} | Net R = {res_dynamic_nested['net_r']:.2f}R | Exp = {res_dynamic_nested['exp_r']:.4f}R | WR = {res_dynamic_nested['wr']:.2f}% | PF = {res_dynamic_nested['pf']:.3f} | MaxDD = {res_dynamic_nested['max_dd_r']:.2f}R")

    # 5. VALIDACIÓN WALK-FORWARD ANIDADA EN 3 VENTANAS TEMPORALES INDEPENDIENTES
    print("\n" + "=" * 80)
    print("5. MALAYSIAN SNR: WALK-FORWARD MULTI-VENTANA ANIDADO")
    print("=" * 80)
    t_min = df_snr_sorted['time'].min()
    t_max = df_snr_sorted['time'].max()
    step = (t_max - t_min) / 3
    w1 = df_snr_sorted[df_snr_sorted['time'] < t_min + step].copy()
    w2 = df_snr_sorted[(df_snr_sorted['time'] >= t_min + step) & (df_snr_sorted['time'] < t_min + 2*step)].copy()
    w3 = df_snr_sorted[df_snr_sorted['time'] >= t_min + 2*step].copy()

    # Paso 1: Train en W1 -> Test OOS en W2
    w1_pos_assets = set(w1.groupby('symbol')['rr'].sum()[lambda x: x > 0].index)
    test_w2_nested = w2[w2['symbol'].isin(w1_pos_assets) & (w2['body_ratio'] >= 0.50) & (w2['adx'] >= 20.0)]
    m_w2_nested = compute_metrics(test_w2_nested['rr'])
    print(f"Paso 1 (Train W1 -> Test OOS W2):")
    print(f"  Activos aprendidos en W1: {w1_pos_assets}")
    print(f"  Resultado OOS en W2: N={m_w2_nested['trades']} | Net R={m_w2_nested['net_r']:.2f}R | PF={m_w2_nested['pf']:.3f} | MaxDD={m_w2_nested['max_dd_r']:.2f}R")

    # Paso 2: Train en W1+W2 -> Test OOS en W3
    w12 = pd.concat([w1, w2])
    w12_pos_assets = set(w12.groupby('symbol')['rr'].sum()[lambda x: x > 0].index)
    test_w3_nested = w3[w3['symbol'].isin(w12_pos_assets) & (w3['body_ratio'] >= 0.50) & (w3['adx'] >= 20.0)]
    m_w3_nested = compute_metrics(test_w3_nested['rr'])
    print(f"\nPaso 2 (Train W1+W2 -> Test OOS W3):")
    print(f"  Activos aprendidos en W1+W2: {w12_pos_assets}")
    print(f"  Resultado OOS en W3: N={m_w3_nested['trades']} | Net R={m_w3_nested['net_r']:.2f}R | PF={m_w3_nested['pf']:.3f} | MaxDD={m_w3_nested['max_dd_r']:.2f}R")

    # 6. ANÁLISIS DE SENSIBILIDAD A COSTOS Y ESTRÉS DE LA VARIANTE +13.62 R
    print("\n" + "=" * 80)
    print("6. MALAYSIAN SNR: SENSIBILIDAD A COSTOS DE LA VARIANTE +13.62 R (HOLDOUT)")
    print("=" * 80)
    var_90 = test_snr[mask_body_test & mask_adx_test & mask_pruning_test]
    
    print("Variante Poda + Body/ADX con Escenario 1 Permitido (N=90):")
    cost_scenarios = [
        (0.00, 1.00, "Base (Costos medidos de MT5 ya incorporados)"),
        (0.02, 1.00, "Deslizamiento leve (0.02 R / ~0.5 pips)"),
        (0.05, 1.00, "Deslizamiento moderado (0.05 R / ~1-2 pips)"),
        (0.10, 1.00, "Deslizamiento severo (0.10 R / ~3-4 pips)"),
        (0.00, 1.15, "Gap SL adverso (15% deslizamiento en stop outs)"),
        (0.05, 1.15, "Estrés combinado (0.05 R deslizamiento + 15% Gap SL)"),
        (0.10, 1.20, "Estrés extremo (0.10 R deslizamiento + 20% Gap SL)"),
    ]
    for slip, gap, desc in cost_scenarios:
        adj_s = stress_costs(var_90['rr'], slippage_r=slip, gap_sl_factor=gap)
        m = compute_metrics(adj_s)
        print(f"  - {desc:<55} | Net R = {m['net_r']:6.2f}R | PF = {m['pf']:5.3f} | MaxDD = {m['max_dd_r']:5.2f}R")

    # 7. INCERTIDUMBRE STATÍSTICA (BOOTSTRAP 1.000 ITERACIONES)
    print("\n" + "=" * 80)
    print("7. ESTIMACIÓN DE INCERTIDUMBRE BOOTSTRAP (1.000 RESAMPLES)")
    print("=" * 80)
    boot_res = bootstrap_ci(var_90['rr'], n_boot=1000)
    print(f"Variante +13.62 R (N=90) en Holdout:")
    print(f"  - Media de R: {var_90['rr'].mean():.4f}R")
    print(f"  - Intervalo de Confianza 95% para Media de R: {boot_res['mean_ci']}")
    print(f"  - Intervalo de Confianza 95% para Profit Factor: {boot_res['pf_ci']}")
    print(f"  - ¿El intervalo de confianza cruza cero?: {'SÍ' if boot_res['mean_ci'][0] < 0 < boot_res['mean_ci'][1] else 'NO'}")

    # 8. ICT ABLACIÓN AISLADA DE JUMP 25 Y BODY RATIO
    print("\n" + "=" * 80)
    print("8. ICT: ABLACIONES AISLADAS (UNIVERSO CANÓNICO 15 SÍMBOLOS)")
    print("=" * 80)
    df_ict_raw = pd.read_csv(PROJECT_ROOT / "storage" / "analysis" / "ict_faithful_trades.csv")
    ict_canonical = sorted(list(set(s.replace('micro', '') for s in PRUNED_ASSET_UNIVERSE['ICT'])))
    df_ict_raw['time'] = pd.to_datetime(df_ict_raw['time'], utc=True)
    df_ict_raw['exit_time'] = df_ict_raw['time'] + pd.to_timedelta(df_ict_raw['bars'] * 5, unit='m')
    df_ict = df_ict_raw[df_ict_raw['symbol'].isin(ict_canonical)].sort_values('time').reset_index(drop=True)

    split_ict = int(len(df_ict) * 0.60)
    train_ict = df_ict.iloc[:split_ict].copy()
    test_ict = df_ict.iloc[split_ict:].copy()

    ict_variants = [
        ("Mecánica Base OOS", test_ict),
        ("Solo Exclusión Jump 25 OOS", test_ict[test_ict['symbol'] != 'Jump 25 Index']),
        ("Solo Body Ratio > 0.50 OOS", test_ict[test_ict['body_ratio'] > 0.50]),
        ("Jump 25 Excluido + Body > 0.50 (Sin Filtros Horarios) OOS", test_ict[(test_ict['symbol'] != 'Jump 25 Index') & (test_ict['body_ratio'] > 0.50)]),
        ("Filtros Previamente Reportados (Con Exclusión Retrospectiva Hora 8)", test_ict[(~test_ict['ny_hour'].isin([7, 8])) & (~test_ict['ny_hour'].isin([0, 6, 20, 22])) & (test_ict['symbol'] != 'Jump 25 Index') & (test_ict['body_ratio'] > 0.50)]),
    ]
    for name, sub in ict_variants:
        m = compute_metrics(sub['rr'])
        print(f"  - {name:<65} | N={m['trades']:3d} | Net R={m['net_r']:6.2f}R | Exp={m['exp_r']:7.4f}R | PF={m['pf']:5.3f} | MaxDD={m['max_dd_r']:5.2f}R")

if __name__ == "__main__":
    main()
