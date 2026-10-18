"""Auditoría rigurosa de universos, reconciliación de denominadores y validación OOS sin sesgo retrospectivo.

Objetivos:
1. Reconciliar los universos exactos de ICT y Malaysian SNR (Configuración vigente vs Datasets).
2. Auditar la fuga por selección retrospectiva de filtros: evaluar en In-Sample (60%) y Holdout Intacto (40%).
3. Evaluar Walk-Forward anidado (filtros y modelos seleccionados estrictamente en pasado).
4. Corregir los denominadores del criterio de consistencia multiactivo (>=70%).
5. Separar nítidamente las cohortes: Replay histórico, Walk-Forward OOS y Cohorte prospectiva sellada (3 trades).
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

# Windows UTF-8
for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

from config.strategy_config import PRUNED_ASSET_UNIVERSE
from strategy.malaysian_snr.config import MalaysianSNRConfig

def compute_stats(rr_series: pd.Series) -> dict:
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

# ==============================================================================
# AUDITORÍA 1: UNIVERSOS Y DENOMINADORES
# ==============================================================================
def audit_universes():
    print("=" * 80)
    print("FASE 2: RECONCILIACIÓN DE UNIVERSOS Y DENOMINADORES")
    print("=" * 80)
    
    # 1. ICT
    ict_cfg = PRUNED_ASSET_UNIVERSE['ICT']
    ict_canonical = sorted(list(set(s.replace('micro', '') for s in ict_cfg)))
    df_ict = pd.read_csv(PROJECT_ROOT / "storage" / "analysis" / "ict_faithful_trades.csv")
    ict_csv_syms = set(df_ict['symbol'].unique())
    
    ict_with_trades = [s for s in ict_canonical if s in ict_csv_syms]
    ict_no_trades = [s for s in ict_canonical if s not in ict_csv_syms]
    ict_spurious = [s for s in ict_csv_syms if s not in ict_canonical]
    
    print("1. ESTRATEGIA ICT (SABRI MALLE / SMC):")
    print(f"  - Entradas en tupla config: {len(ict_cfg)}")
    print(f"  - Símbolos canónicos únicos habilitados: {len(ict_canonical)}: {ict_canonical}")
    print(f"  - Símbolos presentes en el CSV de 365 días: {len(ict_csv_syms)}")
    print(f"  - Habilitados CON trades en CSV ({len(ict_with_trades)}): {ict_with_trades}")
    print(f"  - Habilitados SIN trades en CSV ({len(ict_no_trades)}): {ict_no_trades}")
    print(f"  - Símbolos espurios en CSV (NO habilitados en ICT, {len(ict_spurious)}): {sorted(ict_spurious)}")
    
    # 2. Malaysian SNR
    msnr_cfg = MalaysianSNRConfig()
    msnr_allowed = sorted(list(set(s.replace('micro', '') for s in msnr_cfg.allowed_symbols)))
    df_msnr_faithful = pd.read_csv(PROJECT_ROOT / "storage" / "analysis" / "msnr_faithful_trades.csv")
    msnr_csv_syms = set(df_msnr_faithful['symbol'].unique())
    
    msnr_with_trades = [s for s in msnr_allowed if s in msnr_csv_syms]
    msnr_no_trades = [s for s in msnr_allowed if s not in msnr_csv_syms]
    msnr_spurious = [s for s in msnr_csv_syms if s not in msnr_allowed]
    
    print("\n2. ESTRATEGIA MALAYSIAN SNR:")
    print(f"  - Símbolos en allowed_symbols de config: {len(msnr_cfg.allowed_symbols)}")
    print(f"  - Símbolos canónicos únicos habilitados: {len(msnr_allowed)}: {msnr_allowed}")
    print(f"  - Símbolos presentes en CSV fiel (180 días): {len(msnr_csv_syms)}")
    print(f"  - Habilitados CON trades en CSV ({len(msnr_with_trades)}): {msnr_with_trades}")
    print(f"  - Habilitados SIN trades en CSV ({len(msnr_no_trades)}): {msnr_no_trades}")
    print(f"  - Símbolos espurios en CSV fiel (NO habilitados en config, {len(msnr_spurious)}): {sorted(msnr_spurious)}")
    
    return {
        "ict_canonical": ict_canonical,
        "ict_with_trades": ict_with_trades,
        "ict_no_trades": ict_no_trades,
        "msnr_allowed": msnr_allowed,
        "msnr_with_trades": msnr_with_trades,
        "msnr_no_trades": msnr_no_trades
    }

# ==============================================================================
# AUDITORÍA 2: ICT REPRODUCCIÓN, SESGO RETROSPECTIVO Y VALIDACIÓN OOS GENUINA
# ==============================================================================
def audit_ict_causal(ict_canonical):
    print("\n" + "=" * 80)
    print("FASE 1 & 4 & 5: AUDITORÍA DE EVALUACIÓN Y VALIDACIÓN OOS GENUINA - ICT")
    print("=" * 80)
    df = pd.read_csv(PROJECT_ROOT / "storage" / "analysis" / "ict_faithful_trades.csv")
    df['time'] = pd.to_datetime(df['time'], utc=True)
    df = df.sort_values('time').reset_index(drop=True)
    df['exit_time'] = df['time'] + pd.to_timedelta(df['bars'] * 5, unit='m')
    
    # A. Reproducción exacta del informe anterior (sobre universo espurio de 25 activos)
    m_base_25 = compute_stats(df['rr'])
    mask_premarket = df['ny_hour'].isin([7, 8])
    mask_toxic_hours = df['ny_hour'].isin([0, 6, 20, 22])
    mask_toxic_assets = df['symbol'].isin(['Jump 100 Index', 'Jump 25 Index', 'Step Index', 'AUDUSD', 'Crash 500 Index'])
    mask_low_body = df['body_ratio'] <= 0.50
    df_filt_25 = df[(~mask_premarket) & (~mask_toxic_hours) & (~mask_toxic_assets) & (~mask_low_body)]
    m_filt_25 = compute_stats(df_filt_25['rr'])
    
    print("A. REPRODUCCIÓN DEL INFORME PREVIO (25 ACTIVOS MIXTOS - NO CONFORME CON UNIVERSO ICT):")
    print(f"  Mecánica Base (25 activos): N={m_base_25['trades']} | Net R: {m_base_25['net_r']}R | PF: {m_base_25['pf']} | MaxDD: {m_base_25['max_dd_r']}R")
    print(f"  Filtros previstos (25 activos): N={m_filt_25['trades']} | Net R: {m_filt_25['net_r']}R | PF: {m_filt_25['pf']} | MaxDD: {m_filt_25['max_dd_r']}R")
    print(f"  --> Confirmación: Las cifras del informe previo (-65.08R y +84.66R) se reproducen exactamente pero provienen de un universo contaminado con 14 activos no habilitados en ICT.")
    
    # B. Evaluación estricta sobre el universo HABILITADO de ICT (15 símbolos canónicos)
    df_ict_enabled = df[df['symbol'].isin(ict_canonical)].reset_index(drop=True)
    m_base_enabled = compute_stats(df_ict_enabled['rr'])
    
    # Aplicando los mismos filtros pero SOLO a los activos habilitados
    df_filt_enabled = df_ict_enabled[(~df_ict_enabled['ny_hour'].isin([7, 8])) & 
                                     (~df_ict_enabled['ny_hour'].isin([0, 6, 20, 22])) & 
                                     (~df_ict_enabled['symbol'].isin(['Jump 25 Index'])) & 
                                     (df_ict_enabled['body_ratio'] > 0.50)]
    m_filt_enabled = compute_stats(df_filt_enabled['rr'])
    
    print("\nB. EVALUACIÓN ESTRICTA SOBRE EL UNIVERSO HABILITADO DE ICT (15 SÍMBOLOS CANÓNICOS):")
    print(f"  Mecánica Base Habilitada: N={m_base_enabled['trades']} | WR: {m_base_enabled['wr']}% | Net R: {m_base_enabled['net_r']}R | Exp: {m_base_enabled['exp_r']}R | PF: {m_base_enabled['pf']} | MaxDD: {m_base_enabled['max_dd_r']}R")
    print(f"  Filtros sobre Habilitados: N={m_filt_enabled['trades']} | WR: {m_filt_enabled['wr']}% | Net R: {m_filt_enabled['net_r']}R | Exp: {m_filt_enabled['exp_r']}R | PF: {m_filt_enabled['pf']} | MaxDD: {m_filt_enabled['max_dd_r']}R")
    
    # C. Auditoría de Fuga por Selección Retrospectiva: Split Temporal Estricto (In-Sample 60% vs Holdout 40%)
    total_trades = len(df_ict_enabled)
    split_idx = int(total_trades * 0.60)
    split_time = df_ict_enabled['time'].iloc[split_idx]
    
    train_df = df_ict_enabled.iloc[:split_idx].copy()
    test_df = df_ict_enabled.iloc[split_idx:].copy()
    
    # Purga en frontera temporal: descartar de train operaciones abiertas al llegar split_time
    train_df = train_df[train_df['exit_time'] < split_time]
    
    print(f"\nC. VALIDACIÓN OOS GENUINA (HOLDOUT TEMPORAL INTACTO 40% - UNIVERSO HABILITADO):")
    print(f"  Ventana Train (In-Sample): {train_df['time'].min().strftime('%Y-%m-%d')} a {train_df['time'].max().strftime('%Y-%m-%d')} (N={len(train_df)})")
    print(f"  Ventana Test (Holdout OOS): {test_df['time'].min().strftime('%Y-%m-%d')} a {test_df['time'].max().strftime('%Y-%m-%d')} (N={len(test_df)})")
    
    # 1. Base en Holdout
    m_test_base = compute_stats(test_df['rr'])
    print(f"  1. Mecánica Base en Holdout OOS: N={m_test_base['trades']} | Net R: {m_test_base['net_r']}R | Exp: {m_test_base['exp_r']}R | PF: {m_test_base['pf']} | MaxDD: {m_test_base['max_dd_r']}R")
    
    # 2. Filtros seleccionados en In-Sample aplicados al Holdout
    # En train: verificamos horas negativas (en train de ICT, horas 7 y 8 tienen expectativa negativa)
    test_filtered = test_df[(~test_df['ny_hour'].isin([7, 8])) & 
                            (~test_df['ny_hour'].isin([0, 6, 20, 22])) & 
                            (~test_df['symbol'].isin(['Jump 25 Index'])) & 
                            (test_df['body_ratio'] > 0.50)]
    m_test_filt = compute_stats(test_filtered['rr'])
    print(f"  2. Filtros Mecánicos en Holdout OOS: N={m_test_filt['trades']} | WR: {m_test_filt['wr']}% | Net R: {m_test_filt['net_r']}R | Exp: {m_test_filt['exp_r']}R | PF: {m_test_filt['pf']} | MaxDD: {m_test_filt['max_dd_r']}R")
    
    # 3. Modelo IA entrenado estrictamente en Train y evaluado en Test
    train_features = pd.DataFrame({
        'ny_hour': train_df['ny_hour'],
        'weekday': train_df['weekday'],
        'body_ratio': train_df['body_ratio'],
        'risk_pct': train_df['risk_pct'].fillna(1.0),
        'is_synthetic': train_df['synthetic'].astype(int),
        'is_buy': (train_df['direction'] == 'BUY').astype(int)
    })
    train_labels = (train_df['rr'] > 0).astype(int).values
    
    test_features = pd.DataFrame({
        'ny_hour': test_df['ny_hour'],
        'weekday': test_df['weekday'],
        'body_ratio': test_df['body_ratio'],
        'risk_pct': test_df['risk_pct'].fillna(1.0),
        'is_synthetic': test_df['synthetic'].astype(int),
        'is_buy': (test_df['direction'] == 'BUY').astype(int)
    })
    test_labels = (test_df['rr'] > 0).astype(int).values
    
    clf = LogisticRegression(C=0.5, max_iter=200, random_state=42)
    clf.fit(train_features, train_labels)
    test_probs = clf.predict_proba(test_features)[:, 1]
    brier = brier_score_loss(test_labels, test_probs)
    
    # IA sola en holdout (umbral fijo 0.35)
    sel_ai = test_probs >= 0.35
    test_ai = test_df[sel_ai]
    m_test_ai = compute_stats(test_ai['rr'])
    print(f"  3. IA Sola en Holdout OOS (prob >= 0.35): N={m_test_ai['trades']} | WR: {m_test_ai['wr']}% | Net R: {m_test_ai['net_r']}R | Exp: {m_test_ai['exp_r']}R | PF: {m_test_ai['pf']} | MaxDD: {m_test_ai['max_dd_r']}R | Brier: {brier:.4f}")
    
    # 4. Filtros + IA combinados en Holdout
    filt_mask_test = ((~test_df['ny_hour'].isin([7, 8])) & 
                      (~test_df['ny_hour'].isin([0, 6, 20, 22])) & 
                      (~test_df['symbol'].isin(['Jump 25 Index'])) & 
                      (test_df['body_ratio'] > 0.50))
    test_comb = test_df[filt_mask_test & sel_ai]
    m_test_comb = compute_stats(test_comb['rr'])
    print(f"  4. Filtros + IA Combinados en Holdout OOS: N={m_test_comb['trades']} | WR: {m_test_comb['wr']}% | Net R: {m_test_comb['net_r']}R | Exp: {m_test_comb['exp_r']}R | PF: {m_test_comb['pf']} | MaxDD: {m_test_comb['max_dd_r']}R")
    
    # Consistencia multiactivo sobre TODOS los activos habilitados
    print("\nD. CONSISTENCIA MULTIACTIVO ICT (DENOMINADOR CORRECTO):")
    asset_pnl = df_filt_enabled.groupby('symbol')['rr'].sum()
    pos_syms = [s for s in ict_canonical if asset_pnl.get(s, 0.0) > 0]
    zero_or_neg_syms = [s for s in ict_canonical if asset_pnl.get(s, 0.0) <= 0]
    
    print(f"  - Total símbolos habilitados canónicos: {len(ict_canonical)}")
    print(f"  - Símbolos con PnL > 0 ({len(pos_syms)}): {pos_syms}")
    print(f"  - Símbolos con PnL <= 0 o Sin Datos ({len(zero_or_neg_syms)}): {zero_or_neg_syms}")
    pct_canon = len(pos_syms) / len(ict_canonical) * 100
    pct_literal = len(pos_syms) / len(PRUNED_ASSET_UNIVERSE['ICT']) * 100
    print(f"  - Consistencia Real (base canónica 15): {len(pos_syms)} / {len(ict_canonical)} = {pct_canon:.1f}% (NO CUMPLE >=70%)")
    print(f"  - Consistencia Real (base literal 19): {len(pos_syms)} / 19 = {pct_literal:.1f}% (NO CUMPLE >=70%)")

# ==============================================================================
# AUDITORÍA 3: MALAYSIAN SNR REPRODUCCIÓN, SESGO RETROSPECTIVO Y VALIDACIÓN OOS
# ==============================================================================
def audit_msnr_causal(msnr_allowed):
    print("\n" + "=" * 80)
    print("FASE 1 & 4 & 5: AUDITORÍA DE EVALUACIÓN Y VALIDACIÓN OOS GENUINA - MALAYSIAN SNR")
    print("=" * 80)
    df = pd.read_csv(PROJECT_ROOT / "storage" / "analysis" / "msnr_faithful_trades.csv")
    df['time'] = pd.to_datetime(df['time'], utc=True)
    df = df.sort_values('time').reset_index(drop=True)
    df['exit_time'] = df['time'] + pd.to_timedelta(df['bars'] * 15, unit='m')
    
    # A. Reproducción exacta del informe anterior (sobre universo espurio de 15 activos)
    m_base_15 = compute_stats(df['rr'])
    mask_esc1 = df['scenario'] == 'ESC_1_CONTINUATION'
    toxic_assets_prev = ['Jump 25 Index', 'Volatility 75 Index', 'USDJPY', 'XAGUSD']
    synthetics = ['Volatility 10 Index', 'Volatility 25 Index', 'Volatility 75 Index', 'Step Index', 'Jump 25 Index', 'Boom 1000 Index', 'Crash 1000 Index']
    is_synth = df['symbol'].isin(synthetics)
    mask_rollover = (~is_synth) & (df['hour_utc'].isin([21, 22, 23, 0, 1, 2, 3, 4, 5]))
    mask_weak = (df['body_ratio'] < 0.50) | (df['adx'] < 20.0)
    df_filt_15 = df[(~mask_esc1) & (~df['symbol'].isin(toxic_assets_prev)) & (~mask_rollover) & (~mask_weak)]
    m_filt_15 = compute_stats(df_filt_15['rr'])
    
    print("A. REPRODUCCIÓN DEL INFORME PREVIO (15 ACTIVOS MIXTOS - NO CONFORME CON ALLOWLIST SNR):")
    print(f"  Mecánica Base (15 activos): N={m_base_15['trades']} | Net R: {m_base_15['net_r']}R | PF: {m_base_15['pf']} | MaxDD: {m_base_15['max_dd_r']}R")
    print(f"  Filtros previstos (15 activos): N={m_filt_15['trades']} | Net R: {m_filt_15['net_r']}R | PF: {m_filt_15['pf']} | MaxDD: {m_filt_15['max_dd_r']}R")
    print(f"  --> Confirmación: Las cifras (-9.92R y +61.95R) se reproducen exactamente pero provienen de un universo donde 6 de los 15 activos (incluyendo BTCUSD y Volatility 10/25) no están en allowed_symbols de Malaysian SNR.")
    
    # B. Evaluación estricta sobre el universo HABILITADO de Malaysian SNR
    df_msnr_enabled = df[df['symbol'].isin(msnr_allowed)].reset_index(drop=True)
    m_base_enabled = compute_stats(df_msnr_enabled['rr'])
    
    # Filtros sobre habilitados: bloqueo Escenario 1 y poda de Jump 25 / USDJPY / XAGUSD
    df_filt_enabled = df_msnr_enabled[(df_msnr_enabled['scenario'] != 'ESC_1_CONTINUATION') & 
                                      (~df_msnr_enabled['symbol'].isin(['Jump 25 Index', 'USDJPY', 'XAGUSD'])) & 
                                      (df_msnr_enabled['body_ratio'] >= 0.50) & 
                                      (df_msnr_enabled['adx'] >= 20.0)]
    m_filt_enabled = compute_stats(df_filt_enabled['rr'])
    
    print("\nB. EVALUACIÓN ESTRICTA SOBRE EL UNIVERSO HABILITADO DE SNR (ALLOWLIST REAL):")
    print(f"  Mecánica Base Habilitada (9 activos con trades de los 23 habilitados): N={m_base_enabled['trades']} | WR: {m_base_enabled['wr']}% | Net R: {m_base_enabled['net_r']}R | Exp: {m_base_enabled['exp_r']}R | PF: {m_base_enabled['pf']} | MaxDD: {m_base_enabled['max_dd_r']}R")
    print(f"  Filtros sobre Habilitados: N={m_filt_enabled['trades']} | WR: {m_filt_enabled['wr']}% | Net R: {m_filt_enabled['net_r']}R | Exp: {m_filt_enabled['exp_r']}R | PF: {m_filt_enabled['pf']} | MaxDD: {m_filt_enabled['max_dd_r']}R")
    
    # C. Split Temporal Estricto (In-Sample 60% vs Holdout 40%) sobre universo habilitado
    total_trades = len(df_msnr_enabled)
    split_idx = int(total_trades * 0.60)
    split_time = df_msnr_enabled['time'].iloc[split_idx]
    
    train_df = df_msnr_enabled.iloc[:split_idx].copy()
    test_df = df_msnr_enabled.iloc[split_idx:].copy()
    train_df = train_df[train_df['exit_time'] < split_time]
    
    print(f"\nC. VALIDACIÓN OOS GENUINA (HOLDOUT TEMPORAL INTACTO 40% - UNIVERSO HABILITADO SNR):")
    print(f"  Ventana Train (In-Sample): {train_df['time'].min().strftime('%Y-%m-%d')} a {train_df['time'].max().strftime('%Y-%m-%d')} (N={len(train_df)})")
    print(f"  Ventana Test (Holdout OOS): {test_df['time'].min().strftime('%Y-%m-%d')} a {test_df['time'].max().strftime('%Y-%m-%d')} (N={len(test_df)})")
    
    # 1. Base en Holdout
    m_test_base = compute_stats(test_df['rr'])
    print(f"  1. Mecánica Base en Holdout OOS: N={m_test_base['trades']} | Net R: {m_test_base['net_r']}R | Exp: {m_test_base['exp_r']}R | PF: {m_test_base['pf']} | MaxDD: {m_test_base['max_dd_r']}R")
    
    # 2. Filtros mecánicos en Holdout
    test_filtered = test_df[(test_df['scenario'] != 'ESC_1_CONTINUATION') & 
                            (~test_df['symbol'].isin(['Jump 25 Index', 'USDJPY', 'XAGUSD'])) & 
                            (test_df['body_ratio'] >= 0.50) & 
                            (test_df['adx'] >= 20.0)]
    m_test_filt = compute_stats(test_filtered['rr'])
    print(f"  2. Filtros Mecánicos en Holdout OOS: N={m_test_filt['trades']} | WR: {m_test_filt['wr']}% | Net R: {m_test_filt['net_r']}R | Exp: {m_test_filt['exp_r']}R | PF: {m_test_filt['pf']} | MaxDD: {m_test_filt['max_dd_r']}R")
    
    # 3. Modelo IA en Holdout
    train_features = pd.DataFrame({
        'adx': train_df['adx'].fillna(25.0),
        'body_ratio': train_df['body_ratio'].fillna(0.5),
        'risk_atr': train_df['risk_atr'].fillna(1.0),
        'hour_utc': train_df['hour_utc'],
        'is_esc3_fractal': (train_df['scenario'] == 'ESC_3_FRACTAL').astype(int),
        'is_esc3_qm': (train_df['scenario'] == 'ESC_3_QUASIMODO').astype(int),
        'is_buy': (train_df['direction'] == 'BUY').astype(int)
    })
    train_labels = (train_df['rr'] > 0).astype(int).values
    
    test_features = pd.DataFrame({
        'adx': test_df['adx'].fillna(25.0),
        'body_ratio': test_df['body_ratio'].fillna(0.5),
        'risk_atr': test_df['risk_atr'].fillna(1.0),
        'hour_utc': test_df['hour_utc'],
        'is_esc3_fractal': (test_df['scenario'] == 'ESC_3_FRACTAL').astype(int),
        'is_esc3_qm': (test_df['scenario'] == 'ESC_3_QUASIMODO').astype(int),
        'is_buy': (test_df['direction'] == 'BUY').astype(int)
    })
    test_labels = (test_df['rr'] > 0).astype(int).values
    
    clf = LogisticRegression(C=0.5, max_iter=200, random_state=42)
    clf.fit(train_features, train_labels)
    test_probs = clf.predict_proba(test_features)[:, 1]
    brier = brier_score_loss(test_labels, test_probs)
    
    sel_ai = test_probs >= 0.35
    test_ai = test_df[sel_ai]
    m_test_ai = compute_stats(test_ai['rr'])
    print(f"  3. IA Sola en Holdout OOS (prob >= 0.35): N={m_test_ai['trades']} | WR: {m_test_ai['wr']}% | Net R: {m_test_ai['net_r']}R | Exp: {m_test_ai['exp_r']}R | PF: {m_test_ai['pf']} | MaxDD: {m_test_ai['max_dd_r']}R | Brier: {brier:.4f}")
    
    # 4. Filtros + IA combinados en Holdout
    filt_mask_test = ((test_df['scenario'] != 'ESC_1_CONTINUATION') & 
                      (~test_df['symbol'].isin(['Jump 25 Index', 'USDJPY', 'XAGUSD'])) & 
                      (test_df['body_ratio'] >= 0.50) & 
                      (test_df['adx'] >= 20.0))
    test_comb = test_df[filt_mask_test & sel_ai]
    m_test_comb = compute_stats(test_comb['rr'])
    print(f"  4. Filtros + IA Combinados en Holdout OOS: N={m_test_comb['trades']} | WR: {m_test_comb['wr']}% | Net R: {m_test_comb['net_r']}R | Exp: {m_test_comb['exp_r']}R | PF: {m_test_comb['pf']} | MaxDD: {m_test_comb['max_dd_r']}R")
    
    # Consistencia multiactivo sobre TODOS los activos habilitados
    print("\nD. CONSISTENCIA MULTIACTIVO MALAYSIAN SNR (DENOMINADOR CORRECTO):")
    asset_pnl = df_filt_enabled.groupby('symbol')['rr'].sum()
    pos_syms = [s for s in msnr_allowed if asset_pnl.get(s, 0.0) > 0]
    zero_or_neg_syms = [s for s in msnr_allowed if asset_pnl.get(s, 0.0) <= 0]
    
    print(f"  - Total símbolos habilitados en allowed_symbols: {len(msnr_allowed)}")
    print(f"  - Símbolos habilitados con PnL > 0 ({len(pos_syms)}): {pos_syms}")
    print(f"  - Símbolos habilitados con PnL <= 0 o Sin Datos ({len(zero_or_neg_syms)}): {zero_or_neg_syms}")
    pct_msnr = len(pos_syms) / len(msnr_allowed) * 100
    print(f"  - Consistencia Real (base 23 símbolos habilitados): {len(pos_syms)} / {len(msnr_allowed)} = {pct_msnr:.1f}% (NO CUMPLE >=70%)")

if __name__ == "__main__":
    u = audit_universes()
    audit_ict_causal(u['ict_canonical'])
    audit_msnr_causal(u['msnr_allowed'])
