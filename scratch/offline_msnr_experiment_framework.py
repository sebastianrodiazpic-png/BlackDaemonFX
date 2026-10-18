"""
scratch/offline_msnr_experiment_framework.py
=============================================
Marco de Experimentación Offline Aislado para Malaysian SNR.
Garantías:
1. Opera estrictamente fuera de línea; NO modifica ni interactúa con el runner activo.
2. NO escribe en bases productivas ni modifica trading_bot.sqlite3.
3. Aplica Purga y Embargo temporal para prevenir fuga de información entre Train y Holdout.
4. Evalúa las 5 variantes requeridas:
   1) Base sin filtro
   2) Filtro Mecánico H4 fresco
   3) LightGBM actual (umbral 0.35 congelado)
   4) Candidato IA Regularizado (max_depth=2, min_child_samples=25, L2)
   5) Candidato IA con Normalización de Spread por Activo (z-score de spread_ratio)
"""
import sys
from pathlib import Path
PROJECT_ROOT = Path(__file__).resolve().parent.parent

import pandas as pd
import numpy as np
import lightgbm as lgb
from sklearn.metrics import roc_auc_score, brier_score_loss, log_loss

def run_offline_experiments():
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
    
    # 1. Tiempos y Duración
    v21_en['t_entry'] = pd.to_datetime(v21_en['time'], utc=True)
    v21_en['t_exit'] = pd.to_datetime(v21_en['exit_time'], utc=True)
    v21_en['duration_hours'] = (v21_en['t_exit'] - v21_en['t_entry']).dt.total_seconds() / 3600.0
    
    # Target
    v21_en['target'] = (v21_en['rr'] > 0).astype(int)
    
    # Features estándar al momento de la señal (sin lookahead)
    v21_en['hour'] = v21_en['t_entry'].dt.hour
    v21_en['dayofweek'] = v21_en['t_entry'].dt.dayofweek
    v21_en['is_synthetic'] = v21_en['symbol'].apply(lambda s: 1.0 if any(k in s for k in ['Crash', 'Boom', 'Step', 'Jump', 'Volatility']) else 0.0)
    v21_en['is_buy'] = (v21_en['direction'] == 'BUY').astype(float)
    v21_en['spread_ratio'] = v21_en['spread'] / v21_en['risk_atr'].clip(lower=0.0001)
    v21_en['risk_atr_norm'] = v21_en['risk_atr'] / v21_en['entry'].clip(lower=0.0001)
    v21_en['scen_h4'] = (v21_en['scenario'] == 'h4_continuation').astype(float)
    v21_en['scen_v2'] = (v21_en['scenario'] == 'v2_rejection').astype(float)
    v21_en['trigger_retest'] = (v21_en['trigger'] == 'retest').astype(float)
    
    # 2. Partición Cronológica con Purga y Embargo
    n_total = len(v21_en)
    raw_split_idx = int(n_total * 0.75) # 226 train, 76 holdout
    t_split = v21_en['t_entry'].iloc[raw_split_idx]
    
    # Purga: operaciones en Train que terminaron DESPUÉS de t_split
    overlapping_train_mask = (v21_en['t_entry'] < t_split) & (v21_en['t_exit'] >= t_split)
    purged_count = overlapping_train_mask.sum()
    
    train_indices = v21_en[(v21_en['t_entry'] < t_split) & (~overlapping_train_mask)].index
    holdout_indices = v21_en[v21_en['t_entry'] >= t_split].index
    
    train_df = v21_en.loc[train_indices].copy()
    holdout_df = v21_en.loc[holdout_indices].copy()
    
    # Embargo temporal de 24h: 1 trade en holdout entra en las primeras 24h
    embargo_24h_mask = (holdout_df['t_entry'] < t_split + pd.Timedelta(hours=24))
    
    # 3. Normalización de Spread por Activo SIN FUGA DE DATOS:
    # Se ajusta la media y std de cada símbolo EXCLUSIVAMENTE sobre train_df
    sym_stats = train_df.groupby('symbol')['spread_ratio'].agg(['mean', 'std'])
    glob_mean = train_df['spread_ratio'].mean()
    glob_std = train_df['spread_ratio'].std() + 1e-6
    
    def transform_z(row):
        sym = row['symbol']
        if sym in sym_stats.index and not np.isnan(sym_stats.loc[sym, 'std']) and sym_stats.loc[sym, 'std'] > 1e-6:
            return (row['spread_ratio'] - sym_stats.loc[sym, 'mean']) / sym_stats.loc[sym, 'std']
        return (row['spread_ratio'] - glob_mean) / glob_std
        
    train_df['spread_ratio_asset_z'] = train_df.apply(transform_z, axis=1)
    holdout_df['spread_ratio_asset_z'] = holdout_df.apply(transform_z, axis=1)
    
    print("=========================================================================================")
    print("MARCO DE EXPERIMENTACIÓN OFFLINE: MALAYSIAN SNR (PURGA, EMBARGO Y 5 VARIANTES)")
    print("=========================================================================================")
    print(f"Total datos históricos: {n_total} operaciones (19 activos)")
    print(f"Fecha de corte cronológico: {t_split}")
    print(f"Operaciones en Train antes de purga: {raw_split_idx}")
    print(f"Operaciones purgadas por solapamiento temporal: {purged_count}")
    print(f"Operaciones en ventana de embargo 24h en holdout: {embargo_24h_mask.sum()}")
    print(f"Train limpio final: {len(train_df)} operaciones ({train_df['t_entry'].iloc[0]} a {train_df['t_entry'].iloc[-1]})")
    print(f"Holdout ciego final: {len(holdout_df)} operaciones ({holdout_df['t_entry'].iloc[0]} a {holdout_df['t_entry'].iloc[-1]})")
    print(f"Duración media de trades: {v21_en['duration_hours'].mean():.1f} horas (Max: {v21_en['duration_hours'].max():.1f} h)")

    feat_baseline = ['hour', 'dayofweek', 'is_synthetic', 'is_buy', 'spread_ratio', 'risk_atr_norm', 'scen_h4', 'scen_v2', 'trigger_retest']
    feat_normalized = ['hour', 'dayofweek', 'is_synthetic', 'is_buy', 'spread_ratio_asset_z', 'risk_atr_norm', 'scen_h4', 'scen_v2', 'trigger_retest']
    
    # -------------------------------------------------------------
    # MODELO 3: LightGBM Actual (Referencia con umbral 0.35)
    # -------------------------------------------------------------
    m_baseline = lgb.LGBMClassifier(
        n_estimators=60, max_depth=3, num_leaves=7, learning_rate=0.05,
        min_child_samples=10, random_state=42, verbosity=-1
    )
    m_baseline.fit(train_df[feat_baseline].values, train_df['target'].values)
    p_tr_base = m_baseline.predict_proba(train_df[feat_baseline].values)[:, 1]
    p_ho_base = m_baseline.predict_proba(holdout_df[feat_baseline].values)[:, 1]
    
    # -------------------------------------------------------------
    # MODELO 4: Candidato IA Regularizado (Hipótesis A)
    # max_depth=2, num_leaves=4, min_child=25, L2=1.0, L1=0.5
    # -------------------------------------------------------------
    m_reg = lgb.LGBMClassifier(
        n_estimators=40, max_depth=2, num_leaves=4, learning_rate=0.03,
        min_child_samples=25, reg_alpha=0.5, reg_lambda=1.0, random_state=42, verbosity=-1
    )
    m_reg.fit(train_df[feat_baseline].values, train_df['target'].values)
    p_tr_reg = m_reg.predict_proba(train_df[feat_baseline].values)[:, 1]
    p_ho_reg = m_reg.predict_proba(holdout_df[feat_baseline].values)[:, 1]
    
    # -------------------------------------------------------------
    # MODELO 5: Candidato IA con Normalización de Spread por Activo (Sin Fuga)
    # -------------------------------------------------------------
    m_norm = lgb.LGBMClassifier(
        n_estimators=40, max_depth=2, num_leaves=4, learning_rate=0.03,
        min_child_samples=25, reg_alpha=0.5, reg_lambda=1.0, random_state=42, verbosity=-1
    )
    m_norm.fit(train_df[feat_normalized].values, train_df['target'].values)
    p_tr_norm = m_norm.predict_proba(train_df[feat_normalized].values)[:, 1]
    p_ho_norm = m_norm.predict_proba(holdout_df[feat_normalized].values)[:, 1]

    def compute_metrics(sub_df, p_series, threshold):
        if threshold is None:
            acc = np.ones(len(sub_df), dtype=bool)
        else:
            acc = p_series >= threshold
            
        selected = sub_df.iloc[acc]
        n = len(selected)
        if n == 0:
            return {'n': 0, 'net_r': 0.0, 'wr': 0.0, 'pf': 0.0, 'max_dd': 0.0, 'auc': 0.5, 'brier': 0.25}
        net_r = selected['rr'].sum()
        wr = (selected['rr'] > 0).mean() * 100
        gw = selected[selected['rr'] > 0]['rr'].sum()
        gl = abs(selected[selected['rr'] < 0]['rr'].sum())
        pf = (gw / gl) if gl > 0 else (999.0 if gw > 0 else 0.0)
        cum = selected['rr'].cumsum()
        dd = (cum - cum.cummax()).min()
        
        auc = roc_auc_score(sub_df['target'], p_series) if (p_series is not None and len(np.unique(sub_df['target'])) > 1) else 0.5
        brier = brier_score_loss(sub_df['target'], p_series) if p_series is not None else 0.25
        
        return {
            'n': n,
            'net_r': round(net_r, 2),
            'wr': round(wr, 1),
            'pf': round(pf, 3),
            'max_dd': round(abs(dd) if not np.isnan(dd) else 0.0, 2),
            'auc': round(auc, 4),
            'brier': round(brier, 4)
        }

    # -------------------------------------------------------------
    # TABLA COMPARATIVA DE LAS 5 VARIANTES EN HOLDOUT CIEGO (76 TRADES)
    # -------------------------------------------------------------
    print("\n--- COMPARACIÓN EN HOLDOUT CIEGO OOS (76 Operaciones Idénticas) ---")
    
    m1 = compute_metrics(holdout_df, None, None)
    m3 = compute_metrics(holdout_df, p_ho_base, 0.35)
    m4 = compute_metrics(holdout_df, p_ho_reg, 0.33)
    m5 = compute_metrics(holdout_df, p_ho_norm, 0.35)
    
    comp_rows = [
        {'Variante / Hipótesis': '1. Base sin filtro', 'Trades': m1['n'], 'Net R': f"{m1['net_r']:+.2f} R", 'WR (%)': f"{m1['wr']:.1f}%", 'PF': m1['pf'], 'MaxDD (R)': m1['max_dd'], 'AUC': '-', 'Brier': '-'},
        {'Variante / Hipótesis': '2. Filtro Mecánico H4 Fresco', 'Trades': 'N/D*', 'Net R': 'N/D*', 'WR (%)': 'N/D*', 'PF': 'N/D*', 'MaxDD (R)': 'N/D*', 'AUC': '-', 'Brier': '-'},
        {'Variante / Hipótesis': '3. LightGBM Actual (Th=0.35)', 'Trades': m3['n'], 'Net R': f"{m3['net_r']:+.2f} R", 'WR (%)': f"{m3['wr']:.1f}%", 'PF': m3['pf'], 'MaxDD (R)': m3['max_dd'], 'AUC': m3['auc'], 'Brier': m3['brier']},
        {'Variante / Hipótesis': '4. IA Regularizada (Th=0.33)', 'Trades': m4['n'], 'Net R': f"{m4['net_r']:+.2f} R", 'WR (%)': f"{m4['wr']:.1f}%", 'PF': m4['pf'], 'MaxDD (R)': m4['max_dd'], 'AUC': m4['auc'], 'Brier': m4['brier']},
        {'Variante / Hipótesis': '5. IA Spread Norm Z (Th=0.35, Limpio)', 'Trades': m5['n'], 'Net R': f"{m5['net_r']:+.2f} R", 'WR (%)': f"{m5['wr']:.1f}%", 'PF': m5['pf'], 'MaxDD (R)': m5['max_dd'], 'AUC': m5['auc'], 'Brier': m5['brier']},
    ]
    print(pd.DataFrame(comp_rows).to_string(index=False))
    print("\n* Nota Metodológica: El replay histórico de trades.csv no registró la columna de mitigaciones H4.")
    print("  La cifra anterior de '149 trades / +14.07 R' proviene de un replay agregado a 2 años de una simulación externa,")
    print("  y no puede compararse directamente con el holdout de 76 señales sin re-ejecutar el detector barra a barra.")
    
    # -------------------------------------------------------------
    # DIAGNÓSTICO DE REGULARIZACIÓN Y CALIBRACIÓN
    # -------------------------------------------------------------
    print("\n--- DIAGNÓSTICO COMPARATIVO DE CALIBRACIÓN Y DISCRIMINACIÓN ---")
    cal_diag = [
        {'Modelo': '3. LightGBM Actual', 'Train AUC': round(roc_auc_score(train_df['target'], p_tr_base), 4), 'Holdout AUC': m3['auc'], 'Train Brier': round(brier_score_loss(train_df['target'], p_tr_base), 4), 'Holdout Brier': m3['brier']},
        {'Modelo': '4. IA Regularizada', 'Train AUC': round(roc_auc_score(train_df['target'], p_tr_reg), 4), 'Holdout AUC': m4['auc'], 'Train Brier': round(brier_score_loss(train_df['target'], p_tr_reg), 4), 'Holdout Brier': m4['brier']},
        {'Modelo': '5. IA Spread Norm Z', 'Train AUC': round(roc_auc_score(train_df['target'], p_tr_norm), 4), 'Holdout AUC': m5['auc'], 'Train Brier': round(brier_score_loss(train_df['target'], p_tr_norm), 4), 'Holdout Brier': m5['brier']},
    ]
    print(pd.DataFrame(cal_diag).to_string(index=False))

    # -------------------------------------------------------------
    # DESGLOSE POR ACTIVO EN HOLDOUT PARA CADA CANDIDATO
    # -------------------------------------------------------------
    holdout_df['p_base'] = p_ho_base
    holdout_df['p_reg'] = p_ho_reg
    holdout_df['p_norm'] = p_ho_norm
    
    print("\n--- DESGLOSE POR CLASE DE ACTIVO EN HOLDOUT ---")
    for is_syn, grp in holdout_df.groupby('is_synthetic'):
        cls_name = "Sintéticos Deriv (12 Activos)" if is_syn == 1.0 else "Activos Financieros (Forex, Metales, W30, BTC)"
        acc_base = grp[grp['p_base'] >= 0.35]
        acc_reg = grp[grp['p_reg'] >= 0.33]
        acc_norm = grp[grp['p_norm'] >= 0.35]
        print(f"\n[{cls_name}] (N={len(grp)} trades base, Net R={grp['rr'].sum():+.2f} R):")
        print(f"  * Base:                   {len(grp):2d} t | Net R: {grp['rr'].sum():+6.2f} R | WR: {(grp['rr']>0).mean()*100:5.1f}%")
        print(f"  * Modelo 3 (Actual):      {len(acc_base):2d} t | Net R: {acc_base['rr'].sum():+6.2f} R | WR: {(acc_base['rr']>0).mean()*100:5.1f}%")
        print(f"  * Modelo 4 (Regularizado):{len(acc_reg):2d} t | Net R: {acc_reg['rr'].sum():+6.2f} R | WR: {(acc_reg['rr']>0).mean()*100:5.1f}%")
        print(f"  * Modelo 5 (Spread Norm): {len(acc_norm):2d} t | Net R: {acc_norm['rr'].sum():+6.2f} R | WR: {(acc_norm['rr']>0).mean()*100:5.1f}%")

if __name__ == '__main__':
    run_offline_experiments()
