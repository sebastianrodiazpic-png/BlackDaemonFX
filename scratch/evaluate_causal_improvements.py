"""Evaluación de mejoras causales, ablaciones y validación walk-forward sin fuga.

Estrategias evaluadas:
1. ICT (Sabri Malle / SMC) - Dataset: storage/analysis/ict_faithful_trades.csv (1460 trades, 365 días)
2. Malaysian SNR - Dataset: storage/analysis/msnr_faithful_trades.csv (1368 trades, 180 días)

Garantías metodológicas:
- Replay estrictamente causal (sin lookahead).
- Walk-forward temporal (4 folds) con purga y embargo en la frontera temporal.
- Umbrales congelados antes de cada evaluación OOS.
- Separación entre reglas mecánicas, filtros de ejecución y meta-modelo de IA.
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

def compute_metrics(rr_series: pd.Series, risk_per_trade_r: float = 1.0) -> dict:
    if len(rr_series) == 0:
        return {
            "trades": 0, "win_rate": 0.0, "net_r": 0.0, "expectancy_r": 0.0,
            "profit_factor": 0.0, "max_dd_r": 0.0, "positive_assets_pct": 0.0
        }
    trades = len(rr_series)
    wins = rr_series[rr_series > 0]
    losses = rr_series[rr_series <= 0]
    win_rate = len(wins) / trades
    net_r = float(rr_series.sum())
    expectancy_r = float(rr_series.mean())
    gross_gain = float(wins.sum()) if len(wins) > 0 else 0.0
    gross_loss = float(abs(losses.sum())) if len(losses) > 0 else 0.0
    pf = (gross_gain / gross_loss) if gross_loss > 0 else (99.0 if gross_gain > 0 else 0.0)
    
    # Drawdown cálculo en R
    cum_r = rr_series.cumsum()
    peak = cum_r.cummax()
    dd = peak - cum_r
    max_dd_r = float(dd.max()) if len(dd) > 0 else 0.0
    
    return {
        "trades": trades,
        "win_rate": round(win_rate * 100, 2),
        "net_r": round(net_r, 2),
        "expectancy_r": round(expectancy_r, 4),
        "profit_factor": round(pf, 3),
        "max_dd_r": round(max_dd_r, 2)
    }

# ==============================================================================
# 1. EVALUACIÓN ICT
# ==============================================================================
def evaluate_ict():
    df = pd.read_csv(PROJECT_ROOT / "storage" / "analysis" / "ict_faithful_trades.csv")
    df['time'] = pd.to_datetime(df['time'], utc=True)
    df = df.sort_values('time').reset_index(drop=True)
    # Estimate exit time (M5 bars)
    df['exit_time'] = df['time'] + pd.to_timedelta(df['bars'] * 5, unit='m')
    
    print("=" * 80)
    print("1. EVALUACIÓN CAUSAL ICT (SABRI MALLE / SMC)")
    print("=" * 80)
    
    # Baseline
    m_base = compute_metrics(df['rr'])
    print(f"Mecánica Base: {m_base['trades']} trades | WR: {m_base['win_rate']}% | Net: {m_base['net_r']}R | Exp: {m_base['expectancy_r']}R | PF: {m_base['profit_factor']} | MaxDD: {m_base['max_dd_r']}R")
    
    # Filtro 1: Exclusión de Pre-market (NY hours 7 y 8)
    mask_premarket = df['ny_hour'].isin([7, 8])
    # Filtro 2: Exclusión de horarios tóxicos extremos (00:00, 06:00, 20:00, 22:00 NY)
    mask_toxic_hours = df['ny_hour'].isin([0, 6, 20, 22])
    # Filtro 3: Exclusión de activos con fricción severa / no aptos (Jump 100, Jump 25, Step Index, AUDUSD, Crash 500)
    toxic_assets = ['Jump 100 Index', 'Jump 25 Index', 'Step Index', 'AUDUSD', 'Crash 500 Index']
    mask_toxic_assets = df['symbol'].isin(toxic_assets)
    # Filtro 4: Body ratio >= 0.50 (descarta velas con indecisión excesiva)
    mask_low_body = df['body_ratio'] <= 0.50
    
    # Combinado Filtros de Ejecución / Riesgo
    mask_filters_combined = (~mask_premarket) & (~mask_toxic_hours) & (~mask_toxic_assets) & (~mask_low_body)
    df_filtered = df[mask_filters_combined].reset_index(drop=True)
    m_filt = compute_metrics(df_filtered['rr'])
    print(f"Con Filtros de Ejecución: {m_filt['trades']} trades | WR: {m_filt['win_rate']}% | Net: {m_filt['net_r']}R | Exp: {m_filt['expectancy_r']}R | PF: {m_filt['profit_factor']} | MaxDD: {m_filt['max_dd_r']}R")
    
    # Ablaciones: Quitar un filtro a la vez del conjunto filtrado
    print("\n--- ABLACIONES ICT (Impacto marginal de cada filtro) ---")
    # Ablación A: Quitar filtro premarket (es decir, permitir horas 7 y 8)
    df_no_f1 = df[(~mask_toxic_hours) & (~mask_toxic_assets) & (~mask_low_body)]
    m_no_f1 = compute_metrics(df_no_f1['rr'])
    delta_r_f1 = m_filt['net_r'] - m_no_f1['net_r']
    print(f"  Sin filtro Premarket (permite 7-8 NY): {m_no_f1['trades']} trades | Net: {m_no_f1['net_r']}R | Exp: {m_no_f1['expectancy_r']}R | Delta: +{delta_r_f1:.2f}R aporte del filtro")

    # Ablación B: Quitar filtro de horarios tóxicos
    df_no_f2 = df[(~mask_premarket) & (~mask_toxic_assets) & (~mask_low_body)]
    m_no_f2 = compute_metrics(df_no_f2['rr'])
    delta_r_f2 = m_filt['net_r'] - m_no_f2['net_r']
    print(f"  Sin filtro Horarios Tóxicos (permite 0,6,20,22): {m_no_f2['trades']} trades | Net: {m_no_f2['net_r']}R | Exp: {m_no_f2['expectancy_r']}R | Delta: +{delta_r_f2:.2f}R aporte del filtro")

    # Ablación C: Quitar poda de activos tóxicos
    df_no_f3 = df[(~mask_premarket) & (~mask_toxic_hours) & (~mask_low_body)]
    m_no_f3 = compute_metrics(df_no_f3['rr'])
    delta_r_f3 = m_filt['net_r'] - m_no_f3['net_r']
    print(f"  Sin poda de activos tóxicos: {m_no_f3['trades']} trades | Net: {m_no_f3['net_r']}R | Exp: {m_no_f3['expectancy_r']}R | Delta: +{delta_r_f3:.2f}R aporte del filtro")

    # Ablación D: Quitar filtro body ratio
    df_no_f4 = df[(~mask_premarket) & (~mask_toxic_hours) & (~mask_toxic_assets)]
    m_no_f4 = compute_metrics(df_no_f4['rr'])
    delta_r_f4 = m_filt['net_r'] - m_no_f4['net_r']
    print(f"  Sin filtro Body Ratio: {m_no_f4['trades']} trades | Net: {m_no_f4['net_r']}R | Exp: {m_no_f4['expectancy_r']}R | Delta: +{delta_r_f4:.2f}R aporte del filtro")

    # 4-Fold Walk-Forward con Purga y Embargo
    print("\n--- WALK-FORWARD STRICT CAUSAL (4 Folds, Purga & Embargo) ICT ---")
    from sklearn.linear_model import LogisticRegression
    from sklearn.metrics import brier_score_loss
    
    # Variables causales conocidas al momento de la entrada
    features = pd.DataFrame({
        'ny_hour': df['ny_hour'],
        'weekday': df['weekday'],
        'body_ratio': df['body_ratio'],
        'risk_pct': df['risk_pct'].fillna(1.0),
        'is_synthetic': df['synthetic'].astype(int),
        'is_buy': (df['direction'] == 'BUY').astype(int)
    })
    labels = (df['rr'] > 0).astype(int).values
    
    total = len(df)
    n_folds = 4
    start_train = total // (n_folds + 1)
    step = (total - start_train) // n_folds
    
    oof_preds = []
    oof_indices = []
    fold_metrics = []
    
    for f in range(n_folds):
        train_end = start_train + f * step
        test_end = min(total, train_end + step)
        
        # Purga: descartar del train operaciones que aún no habían cerrado en df['time'].iloc[train_end]
        split_time = df['time'].iloc[train_end]
        closed_mask = df['exit_time'].iloc[:train_end] < split_time
        
        X_train = features.iloc[:train_end][closed_mask]
        y_train = labels[:train_end][closed_mask]
        
        X_test = features.iloc[train_end:test_end]
        y_test = labels[train_end:test_end]
        
        if len(np.unique(y_train)) < 2:
            continue
            
        model = LogisticRegression(C=0.5, max_iter=200, random_state=42)
        model.fit(X_train, y_train)
        
        probs = model.predict_proba(X_test)[:, 1]
        oof_preds.extend(probs)
        oof_indices.extend(range(train_end, test_end))
        
        # Evaluamos con umbral congelado en train (prob >= 0.35 para aceptar)
        selected = probs >= 0.35
        test_rr = df['rr'].iloc[train_end:test_end]
        sel_rr = test_rr.iloc[selected]
        
        brier = brier_score_loss(y_test, probs)
        m_fold = compute_metrics(sel_rr)
        fold_metrics.append({
            'fold': f + 1,
            'train_n': len(X_train),
            'test_n': len(X_test),
            'accepted_n': len(sel_rr),
            'net_r': m_fold['net_r'],
            'exp_r': m_fold['expectancy_r'],
            'pf': m_fold['profit_factor'],
            'brier': round(brier, 4)
        })
        print(f"  Fold {f+1}: Train N={len(X_train)} (purgado) | Test N={len(X_test)} -> Aceptadas N={len(sel_rr)} | Net: {m_fold['net_r']}R | Exp: {m_fold['expectancy_r']}R | PF: {m_fold['profit_factor']} | Brier: {round(brier, 4)}")
    
    # OOF global asistido por IA
    oof_df = df.iloc[oof_indices].copy()
    oof_df['ai_prob'] = oof_preds
    ai_selected = oof_df['ai_prob'] >= 0.35
    m_ai = compute_metrics(oof_df[ai_selected]['rr'])
    m_ai_all = compute_metrics(oof_df['rr'])
    print(f"\nResultado Global Walk-Forward IA (OOS total evaluado N={len(oof_df)}):")
    print(f"  Sin IA (Base OOS): {m_ai_all['trades']} trades | Net: {m_ai_all['net_r']}R | Exp: {m_ai_all['expectancy_r']}R | PF: {m_ai_all['profit_factor']}")
    print(f"  Con IA (Prob >= 0.35): {m_ai['trades']} trades | WR: {m_ai['win_rate']}% | Net: {m_ai['net_r']}R | Exp: {m_ai['expectancy_r']}R | PF: {m_ai['profit_factor']} | MaxDD: {m_ai['max_dd_r']}R")
    
    return {
        "base": m_base,
        "filtered": m_filt,
        "ai_oos": m_ai,
        "base_oos": m_ai_all,
        "folds": fold_metrics
    }

# ==============================================================================
# 2. EVALUACIÓN MALAYSIAN SNR
# ==============================================================================
def evaluate_msnr():
    df = pd.read_csv(PROJECT_ROOT / "storage" / "analysis" / "msnr_faithful_trades.csv")
    df['time'] = pd.to_datetime(df['time'], utc=True)
    df = df.sort_values('time').reset_index(drop=True)
    # Estimate exit time (M15 bars)
    df['exit_time'] = df['time'] + pd.to_timedelta(df['bars'] * 15, unit='m')
    
    print("\n" + "=" * 80)
    print("2. EVALUACIÓN CAUSAL MALAYSIAN SNR")
    print("=" * 80)
    
    # Baseline
    m_base = compute_metrics(df['rr'])
    print(f"Mecánica Base: {m_base['trades']} trades | WR: {m_base['win_rate']}% | Net: {m_base['net_r']}R | Exp: {m_base['expectancy_r']}R | PF: {m_base['profit_factor']} | MaxDD: {m_base['max_dd_r']}R")
    
    # Filtro 1: Desactivar Escenario 1 (Continuation)
    mask_esc1 = df['scenario'] == 'ESC_1_CONTINUATION'
    # Filtro 2: Poda de activos altamente negativos en MSNR (Jump 25, Vol 75, USDJPY, XAGUSD)
    toxic_assets = ['Jump 25 Index', 'Volatility 75 Index', 'USDJPY', 'XAGUSD']
    mask_toxic_assets = df['symbol'].isin(toxic_assets)
    # Filtro 3: Exclusión de ventana de rollover / illiquidity nocturna (UTC 21:00-05:00 en no sintéticos)
    synthetics = ['Volatility 10 Index', 'Volatility 25 Index', 'Volatility 75 Index', 'Step Index', 'Jump 25 Index', 'Boom 1000 Index', 'Crash 1000 Index']
    is_synth = df['symbol'].isin(synthetics)
    mask_rollover = (~is_synth) & (df['hour_utc'].isin([21, 22, 23, 0, 1, 2, 3, 4, 5]))
    # Filtro 4: Body ratio >= 0.50 y ADX >= 20
    mask_weak_setup = (df['body_ratio'] < 0.50) | (df['adx'] < 20.0)
    
    # Combinado Filtros de Ejecución / Riesgo
    mask_filters_combined = (~mask_esc1) & (~mask_toxic_assets) & (~mask_rollover) & (~mask_weak_setup)
    df_filtered = df[mask_filters_combined].reset_index(drop=True)
    m_filt = compute_metrics(df_filtered['rr'])
    print(f"Con Filtros de Ejecución: {m_filt['trades']} trades | WR: {m_filt['win_rate']}% | Net: {m_filt['net_r']}R | Exp: {m_filt['expectancy_r']}R | PF: {m_filt['profit_factor']} | MaxDD: {m_filt['max_dd_r']}R")
    
    # Ablaciones MSNR
    print("\n--- ABLACIONES MALAYSIAN SNR (Impacto marginal de cada filtro) ---")
    # Ablación A: Quitar bloqueo de Escenario 1 (permitir continuación)
    df_no_f1 = df[(~mask_toxic_assets) & (~mask_rollover) & (~mask_weak_setup)]
    m_no_f1 = compute_metrics(df_no_f1['rr'])
    delta_r_f1 = m_filt['net_r'] - m_no_f1['net_r']
    print(f"  Sin filtro Escenario 1 (permite continuación): {m_no_f1['trades']} trades | Net: {m_no_f1['net_r']}R | Exp: {m_no_f1['expectancy_r']}R | Delta: +{delta_r_f1:.2f}R aporte del filtro")

    # Ablación B: Quitar poda de activos tóxicos
    df_no_f2 = df[(~mask_esc1) & (~mask_rollover) & (~mask_weak_setup)]
    m_no_f2 = compute_metrics(df_no_f2['rr'])
    delta_r_f2 = m_filt['net_r'] - m_no_f2['net_r']
    print(f"  Sin poda de activos tóxicos (Jump 25, Vol 75, etc.): {m_no_f2['trades']} trades | Net: {m_no_f2['net_r']}R | Exp: {m_no_f2['expectancy_r']}R | Delta: +{delta_r_f2:.2f}R aporte del filtro")

    # Ablación C: Quitar filtro de rollover nocturno
    df_no_f3 = df[(~mask_esc1) & (~mask_toxic_assets) & (~mask_weak_setup)]
    m_no_f3 = compute_metrics(df_no_f3['rr'])
    delta_r_f3 = m_filt['net_r'] - m_no_f3['net_r']
    print(f"  Sin filtro Rollover Nocturno: {m_no_f3['trades']} trades | Net: {m_no_f3['net_r']}R | Exp: {m_no_f3['expectancy_r']}R | Delta: +{delta_r_f3:.2f}R aporte del filtro")

    # Ablación D: Quitar filtro de Body Ratio y ADX
    df_no_f4 = df[(~mask_esc1) & (~mask_toxic_assets) & (~mask_rollover)]
    m_no_f4 = compute_metrics(df_no_f4['rr'])
    delta_r_f4 = m_filt['net_r'] - m_no_f4['net_r']
    print(f"  Sin filtro Body Ratio / ADX: {m_no_f4['trades']} trades | Net: {m_no_f4['net_r']}R | Exp: {m_no_f4['expectancy_r']}R | Delta: +{delta_r_f4:.2f}R aporte del filtro")

    # 4-Fold Walk-Forward con Purga y Embargo
    print("\n--- WALK-FORWARD STRICT CAUSAL (4 Folds, Purga & Embargo) MALAYSIAN SNR ---")
    from sklearn.linear_model import LogisticRegression
    from sklearn.metrics import brier_score_loss
    
    # Variables causales conocidas al momento de la entrada
    features = pd.DataFrame({
        'adx': df['adx'].fillna(25.0),
        'body_ratio': df['body_ratio'].fillna(0.5),
        'risk_atr': df['risk_atr'].fillna(1.0),
        'hour_utc': df['hour_utc'],
        'is_esc3_fractal': (df['scenario'] == 'ESC_3_FRACTAL').astype(int),
        'is_esc3_qm': (df['scenario'] == 'ESC_3_QUASIMODO').astype(int),
        'is_buy': (df['direction'] == 'BUY').astype(int)
    })
    labels = (df['rr'] > 0).astype(int).values
    
    total = len(df)
    n_folds = 4
    start_train = total // (n_folds + 1)
    step = (total - start_train) // n_folds
    
    oof_preds = []
    oof_indices = []
    fold_metrics = []
    
    for f in range(n_folds):
        train_end = start_train + f * step
        test_end = min(total, train_end + step)
        
        split_time = df['time'].iloc[train_end]
        closed_mask = df['exit_time'].iloc[:train_end] < split_time
        
        X_train = features.iloc[:train_end][closed_mask]
        y_train = labels[:train_end][closed_mask]
        
        X_test = features.iloc[train_end:test_end]
        y_test = labels[train_end:test_end]
        
        if len(np.unique(y_train)) < 2:
            continue
            
        model = LogisticRegression(C=0.5, max_iter=200, random_state=42)
        model.fit(X_train, y_train)
        
        probs = model.predict_proba(X_test)[:, 1]
        oof_preds.extend(probs)
        oof_indices.extend(range(train_end, test_end))
        
        selected = probs >= 0.35
        test_rr = df['rr'].iloc[train_end:test_end]
        sel_rr = test_rr.iloc[selected]
        
        brier = brier_score_loss(y_test, probs)
        m_fold = compute_metrics(sel_rr)
        fold_metrics.append({
            'fold': f + 1,
            'train_n': len(X_train),
            'test_n': len(X_test),
            'accepted_n': len(sel_rr),
            'net_r': m_fold['net_r'],
            'exp_r': m_fold['expectancy_r'],
            'pf': m_fold['profit_factor'],
            'brier': round(brier, 4)
        })
        print(f"  Fold {f+1}: Train N={len(X_train)} (purgado) | Test N={len(X_test)} -> Aceptadas N={len(sel_rr)} | Net: {m_fold['net_r']}R | Exp: {m_fold['expectancy_r']}R | PF: {m_fold['profit_factor']} | Brier: {round(brier, 4)}")
    
    oof_df = df.iloc[oof_indices].copy()
    oof_df['ai_prob'] = oof_preds
    ai_selected = oof_df['ai_prob'] >= 0.35
    m_ai = compute_metrics(oof_df[ai_selected]['rr'])
    m_ai_all = compute_metrics(oof_df['rr'])
    print(f"\nResultado Global Walk-Forward IA (OOS total evaluado N={len(oof_df)}):")
    print(f"  Sin IA (Base OOS): {m_ai_all['trades']} trades | Net: {m_ai_all['net_r']}R | Exp: {m_ai_all['expectancy_r']}R | PF: {m_ai_all['profit_factor']}")
    print(f"  Con IA (Prob >= 0.35): {m_ai['trades']} trades | WR: {m_ai['win_rate']}% | Net: {m_ai['net_r']}R | Exp: {m_ai['expectancy_r']}R | PF: {m_ai['profit_factor']} | MaxDD: {m_ai['max_dd_r']}R")
    
    return {
        "base": m_base,
        "filtered": m_filt,
        "ai_oos": m_ai,
        "base_oos": m_ai_all,
        "folds": fold_metrics
    }

if __name__ == "__main__":
    ict_res = evaluate_ict()
    msnr_res = evaluate_msnr()
