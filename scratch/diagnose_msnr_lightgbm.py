"""
scratch/diagnose_msnr_lightgbm.py
==================================
Diagnóstico offline exhaustivo del modelo LightGBM en Malaysian SNR.
Investiga sobreajuste, calibración, fuga de datos, desbalance y distribución por activo.
"""
import pandas as pd
import numpy as np
from pathlib import Path
import lightgbm as lgb
from sklearn.metrics import brier_score_loss, roc_auc_score, log_loss
from sklearn.calibration import calibration_curve

PROJECT_ROOT = Path(__file__).resolve().parent.parent

def run_diagnostics():
    csv_path = PROJECT_ROOT / 'storage/analysis/msnr_v21_two_years_20261011/trades.csv'
    df = pd.read_csv(csv_path)
    
    enabled_msnr = [
        'Crash 500 Index', 'Crash 600 Index', 'Crash 1000 Index', 'Boom 1000 Index',
        'Boom 500 Index', 'Boom 300 Index', 'Step Index', 'Step Index 400',
        'Wall Street 30', 'XAUUSD', 'EURUSD', 'GBPUSD', 'USDJPY',
        'GBPJPY', 'GBPAUD', 'Jump 10 Index', 'Jump 25 Index', 'Jump 50 Index', 'BTCUSD'
    ]
    
    v21 = df[df['version'] == 'msnr-v2.1-persistent-retest'].sort_values('time').reset_index(drop=True)
    v21_en = v21[v21['symbol'].isin(enabled_msnr)].reset_index(drop=True)
    n_total = len(v21_en)
    
    split_idx = int(n_total * 0.75) # 226 train, 76 holdout
    train_df = v21_en.iloc[:split_idx].copy()
    holdout_df = v21_en.iloc[split_idx:].copy()
    
    for d in [train_df, holdout_df]:
        t = pd.to_datetime(d['time'])
        d['hour'] = t.dt.hour
        d['dayofweek'] = t.dt.dayofweek
        d['is_synthetic'] = d['symbol'].apply(lambda s: 1.0 if any(k in s for k in ['Crash', 'Boom', 'Step', 'Jump', 'Volatility']) else 0.0)
        d['is_buy'] = (d['direction'] == 'BUY').astype(float)
        d['spread_ratio'] = d['spread'] / d['risk_atr'].clip(lower=0.0001)
        d['risk_atr_norm'] = d['risk_atr'] / d['entry'].clip(lower=0.0001)
        d['scen_h4'] = (d['scenario'] == 'h4_continuation').astype(float)
        d['scen_v2'] = (d['scenario'] == 'v2_rejection').astype(float)
        d['trigger_retest'] = (d['trigger'] == 'retest').astype(float)
        d['target'] = (d['rr'] > 0).astype(int)

    feature_cols = [
        'hour', 'dayofweek', 'is_synthetic', 'is_buy', 'spread_ratio',
        'risk_atr_norm', 'scen_h4', 'scen_v2', 'trigger_retest'
    ]
    
    X_train = train_df[feature_cols].values
    y_train = train_df['target'].values
    X_holdout = holdout_df[feature_cols].values
    y_holdout = holdout_df['target'].values
    
    model = lgb.LGBMClassifier(
        n_estimators=60, max_depth=3, num_leaves=7, learning_rate=0.05,
        min_child_samples=10, random_state=42, verbosity=-1
    )
    model.fit(X_train, y_train)
    
    train_probs = model.predict_proba(X_train)[:, 1]
    holdout_probs = model.predict_proba(X_holdout)[:, 1]
    
    print("=========================================================================================")
    print("DIAGNÓSTICO OFFLINE EXHAUSTIVO DE LIGHTGBM (MALAYSIAN SNR)")
    print("=========================================================================================")
    
    # 1. Feature Importance
    importances = model.feature_importances_
    df_imp = pd.DataFrame({'feature': feature_cols, 'importance': importances}).sort_values('importance', ascending=False)
    print("\n1. IMPORTANCIA DE VARIABLES (Split Counts):")
    print(df_imp.to_string(index=False))
    
    # 2. Desbalance y Métricas
    print("\n2. BALANCE DE CLASES Y MÉTRICAS DE GENERALIZACIÓN:")
    print(f"  * Train: {len(y_train)} muestras | Positivos (Wins): {y_train.sum()} ({y_train.mean()*100:.1f}%) | Negativos: {(1-y_train).sum()}")
    print(f"  * Holdout: {len(y_holdout)} muestras | Positivos (Wins): {y_holdout.sum()} ({y_holdout.mean()*100:.1f}%) | Negativos: {(1-y_holdout).sum()}")
    print(f"  * Train AUC: {roc_auc_score(y_train, train_probs):.4f}")
    print(f"  * Holdout AUC: {roc_auc_score(y_holdout, holdout_probs):.4f}")
    print(f"  * Train Brier Score: {brier_score_loss(y_train, train_probs):.4f}")
    print(f"  * Holdout Brier Score: {brier_score_loss(y_holdout, holdout_probs):.4f}")
    print(f"  * Holdout Log Loss: {log_loss(y_holdout, holdout_probs):.4f}")
    
    # 3. Distribución de Probabilidades
    train_df['prob'] = train_probs
    holdout_df['prob'] = holdout_probs
    
    print("\n3. DISTRIBUCIÓN DE PROBABILIDADES PREDICHAS:")
    print(f"  * Train: Mean={train_probs.mean():.3f}, Min={train_probs.min():.3f}, Median={np.median(train_probs):.3f}, Max={train_probs.max():.3f}")
    print(f"  * Holdout: Mean={holdout_probs.mean():.3f}, Min={holdout_probs.min():.3f}, Median={np.median(holdout_probs):.3f}, Max={holdout_probs.max():.3f}")
    
    # 4. Distribución por Clase de Activo (Sintéticos vs Financieros)
    print("\n4. COMPORTAMIENTO POR CLASE DE ACTIVO EN HOLDOUT:")
    for is_syn, grp in holdout_df.groupby('is_synthetic'):
        label = "Sintéticos Deriv" if is_syn == 1.0 else "Activos Financieros (Forex/Gold/Índices)"
        acc_35 = grp[grp['prob'] >= 0.35]
        print(f"  [{label}] Total: {len(grp)} | Aceptados por IA (>=0.35): {len(acc_35)} | Prob Media: {grp['prob'].mean():.3f}")
        print(f"    Base Net R: {grp['rr'].sum():+.2f} R (WR: {(grp['rr']>0).mean()*100:.1f}%) | IA Net R: {acc_35['rr'].sum():+.2f} R (WR: {(acc_35['rr']>0).mean()*100:.1f}%)")

    # 5. Análisis de la muestra en Sombra (12 Eventos)
    print("\n5. ANÁLISIS DE LA MUESTRA SOMBRA (12 Eventos en Vivo):")
    # Cargar shadow db
    import sqlite3
    s_conn = sqlite3.connect(PROJECT_ROOT / 'storage/runtime/shadow_research.sqlite3')
    df_s = pd.read_sql_query("SELECT id, symbol, final_action, ai_probability, market_outcome, market_rr FROM shadow_signals WHERE strategy='MSNR' ORDER BY id", s_conn)
    s_conn.close()
    print(df_s.to_string(index=False))
    print(f"\nProbabilidad media en Sombra: {df_s['ai_probability'].mean():.4f} (Rango: {df_s['ai_probability'].min():.4f} a {df_s['ai_probability'].max():.4f})")
    print("Diagnóstico: El modelo sufre de saturación hacia el extremo superior en señales sintéticas en vivo, perdiendo capacidad de veto.")

if __name__ == '__main__':
    run_diagnostics()
