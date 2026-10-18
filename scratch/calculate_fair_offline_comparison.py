"""
scratch/calculate_fair_offline_comparison.py
============================================
Auditoría y Recálculo Riguroso de las 5 Variantes de Malaysian SNR:
1. Base sin filtros.
2. Filtro H4 fresco solo (análisis de reproducibilidad y datos disponibles).
3. LightGBM actual con umbral 0.35.
4. Modelo regularizado, umbral 0.33.
5. Modelo con spread normalizado por activo (estrictamente ajustado en Train sin fuga), umbral 0.35.

Métricas calculadas sobre particiones idénticas (Train: 226 señales, Holdout: 76 señales).
Desglose por clase de activo y análisis exhaustivo de calibración.
"""
import sys
from pathlib import Path
PROJECT_ROOT = Path(__file__).resolve().parent.parent

import pandas as pd
import numpy as np
import lightgbm as lgb
from sklearn.metrics import roc_auc_score, brier_score_loss, log_loss

def run_fair_comparison():
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
    
    v21_en['t_entry'] = pd.to_datetime(v21_en['time'], utc=True)
    v21_en['t_exit'] = pd.to_datetime(v21_en['exit_time'], utc=True)
    v21_en['target'] = (v21_en['rr'] > 0).astype(int)
    
    # Features estándar calculadas sin lookahead (al momento de la señal)
    v21_en['hour'] = v21_en['t_entry'].dt.hour
    v21_en['dayofweek'] = v21_en['t_entry'].dt.dayofweek
    v21_en['is_synthetic'] = v21_en['symbol'].apply(lambda s: 1.0 if any(k in s for k in ['Crash', 'Boom', 'Step', 'Jump', 'Volatility']) else 0.0)
    v21_en['is_buy'] = (v21_en['direction'] == 'BUY').astype(float)
    v21_en['spread_ratio'] = v21_en['spread'] / v21_en['risk_atr'].clip(lower=0.0001)
    v21_en['risk_atr_norm'] = v21_en['risk_atr'] / v21_en['entry'].clip(lower=0.0001)
    v21_en['scen_h4'] = (v21_en['scenario'] == 'h4_continuation').astype(float)
    v21_en['scen_v2'] = (v21_en['scenario'] == 'v2_rejection').astype(float)
    v21_en['trigger_retest'] = (v21_en['trigger'] == 'retest').astype(float)
    
    # Partición estrictamente cronológica: 75% Train, 25% Holdout
    split_idx = int(n_total * 0.75) # 226 train, 76 holdout
    t_split = v21_en['t_entry'].iloc[split_idx]
    
    train_df = v21_en.iloc[:split_idx].copy()
    holdout_df = v21_en.iloc[split_idx:].copy()
    
    # -------------------------------------------------------------
    # AJUSTE ESTRICTO DE SPREAD NORMALIZADO SIN FUGA (FIT EN TRAIN)
    # -------------------------------------------------------------
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
    
    feat_base = ['hour', 'dayofweek', 'is_synthetic', 'is_buy', 'spread_ratio', 'risk_atr_norm', 'scen_h4', 'scen_v2', 'trigger_retest']
    feat_norm = ['hour', 'dayofweek', 'is_synthetic', 'is_buy', 'spread_ratio_asset_z', 'risk_atr_norm', 'scen_h4', 'scen_v2', 'trigger_retest']
    
    # -------------------------------------------------------------
    # MODELO 3: LightGBM Actual (Th=0.35)
    # -------------------------------------------------------------
    m_actual = lgb.LGBMClassifier(
        n_estimators=60, max_depth=3, num_leaves=7, learning_rate=0.05,
        min_child_samples=10, random_state=42, verbosity=-1
    )
    m_actual.fit(train_df[feat_base].values, train_df['target'].values)
    p_tr_actual = m_actual.predict_proba(train_df[feat_base].values)[:, 1]
    p_ho_actual = m_actual.predict_proba(holdout_df[feat_base].values)[:, 1]
    
    # -------------------------------------------------------------
    # MODELO 4: Candidato IA Regularizado (Th=0.33)
    # -------------------------------------------------------------
    m_reg = lgb.LGBMClassifier(
        n_estimators=40, max_depth=2, num_leaves=4, learning_rate=0.03,
        min_child_samples=25, reg_alpha=0.5, reg_lambda=1.0, random_state=42, verbosity=-1
    )
    m_reg.fit(train_df[feat_base].values, train_df['target'].values)
    p_tr_reg = m_reg.predict_proba(train_df[feat_base].values)[:, 1]
    p_ho_reg = m_reg.predict_proba(holdout_df[feat_base].values)[:, 1]
    
    # -------------------------------------------------------------
    # MODELO 5: Candidato IA Spread Norm Z (Sin Fuga, Th=0.35)
    # -------------------------------------------------------------
    m_norm = lgb.LGBMClassifier(
        n_estimators=40, max_depth=2, num_leaves=4, learning_rate=0.03,
        min_child_samples=25, reg_alpha=0.5, reg_lambda=1.0, random_state=42, verbosity=-1
    )
    m_norm.fit(train_df[feat_norm].values, train_df['target'].values)
    p_tr_norm = m_norm.predict_proba(train_df[feat_norm].values)[:, 1]
    p_ho_norm = m_norm.predict_proba(holdout_df[feat_norm].values)[:, 1]
    
    def compute_kpis(sub_df, probs, threshold):
        if threshold is None:
            mask = np.ones(len(sub_df), dtype=bool)
        else:
            mask = probs >= threshold
            
        sel = sub_df.iloc[mask]
        n = len(sel)
        if n == 0:
            return {'n': 0, 'net_r': 0.0, 'wr': 0.0, 'pf': 0.0, 'max_dd': 0.0, 'auc': 0.5, 'brier': 0.25}
            
        net_r = sel['rr'].sum()
        wr = (sel['rr'] > 0).mean() * 100
        gw = sel[sel['rr'] > 0]['rr'].sum()
        gl = abs(sel[sel['rr'] < 0]['rr'].sum())
        pf = (gw / gl) if gl > 0 else (999.0 if gw > 0 else 0.0)
        cum = sel['rr'].cumsum()
        dd = (cum - cum.cummax()).min()
        
        auc = roc_auc_score(sub_df['target'], probs) if (probs is not None and len(np.unique(sub_df['target'])) > 1) else 0.5
        brier = brier_score_loss(sub_df['target'], probs) if probs is not None else 0.25
        
        return {
            'n': n,
            'net_r': round(net_r, 2),
            'wr': round(wr, 1),
            'pf': round(pf, 3),
            'max_dd': round(abs(dd) if not np.isnan(dd) else 0.0, 2),
            'auc': round(auc, 4),
            'brier': round(brier, 4)
        }

    # Métricas en Holdout
    m1_ho = compute_kpis(holdout_df, None, None)
    m3_ho = compute_kpis(holdout_df, p_ho_actual, 0.35)
    m4_ho = compute_kpis(holdout_df, p_ho_reg, 0.33)
    m5_ho = compute_kpis(holdout_df, p_ho_norm, 0.35)
    
    # Métricas en Train
    m1_tr = compute_kpis(train_df, None, None)
    m3_tr = compute_kpis(train_df, p_tr_actual, 0.35)
    m4_tr = compute_kpis(train_df, p_tr_reg, 0.33)
    m5_tr = compute_kpis(train_df, p_tr_norm, 0.35)
    
    print("=========================================================================================")
    print("REPORTE OFICIAL: AUDITORÍA Y COMPARACIÓN JUSTA DE VARIANTES MALAYSIAN SNR")
    print("=========================================================================================")
    print(f"Universo evaluado: 19 Activos Autorizados en Sombra")
    print(f"Total datos: {n_total} operaciones (Train: {len(train_df)}, Holdout: {len(holdout_df)})")
    print(f"Corte temporal: {t_split}")
    print(f"Ventana Train:   {train_df['t_entry'].iloc[0]} a {train_df['t_entry'].iloc[-1]}")
    print(f"Ventana Holdout: {holdout_df['t_entry'].iloc[0]} a {holdout_df['t_entry'].iloc[-1]}")
    
    print("\n1. COMPARACIÓN EN HOLDOUT CIEGO OOS (76 OPERACIONES IDENTICAS):")
    ho_rows = [
        {'Variante': '1. Base sin filtros', 'Trades': m1_ho['n'], 'Net R': f"{m1_ho['net_r']:+.2f} R", 'WR (%)': f"{m1_ho['wr']:.1f}%", 'PF': m1_ho['pf'], 'MaxDD (R)': m1_ho['max_dd'], 'AUC': '-', 'Brier': '-'},
        {'Variante': '2. Filtro H4 fresco solo', 'Trades': 'N/D*', 'Net R': 'N/D*', 'WR (%)': 'N/D*', 'PF': 'N/D*', 'MaxDD (R)': 'N/D*', 'AUC': '-', 'Brier': '-'},
        {'Variante': '3. LightGBM Actual (0.35)', 'Trades': m3_ho['n'], 'Net R': f"{m3_ho['net_r']:+.2f} R", 'WR (%)': f"{m3_ho['wr']:.1f}%", 'PF': m3_ho['pf'], 'MaxDD (R)': m3_ho['max_dd'], 'AUC': m3_ho['auc'], 'Brier': m3_ho['brier']},
        {'Variante': '4. Modelo Regularizado (0.33)', 'Trades': m4_ho['n'], 'Net R': f"{m4_ho['net_r']:+.2f} R", 'WR (%)': f"{m4_ho['wr']:.1f}%", 'PF': m4_ho['pf'], 'MaxDD (R)': m4_ho['max_dd'], 'AUC': m4_ho['auc'], 'Brier': m4_ho['brier']},
        {'Variante': '5. Modelo Spread Norm Z (0.35, Limpio)', 'Trades': m5_ho['n'], 'Net R': f"{m5_ho['net_r']:+.2f} R", 'WR (%)': f"{m5_ho['wr']:.1f}%", 'PF': m5_ho['pf'], 'MaxDD (R)': m5_ho['max_dd'], 'AUC': m5_ho['auc'], 'Brier': m5_ho['brier']}
    ]
    print(pd.DataFrame(ho_rows).to_string(index=False))
    print("\n* NOTA METODOLÓGICA SOBRE VARIANTE 2 (H4 FRESCO):")
    print("  El dataset histórico v21 (trades.csv) fue ejecutado en M15/H1/D1 sin registrar la columna 'h4_mitigations'.")
    print("  La cifra '149 trades / +14.07 R' reportada previamente corresponde al replay agregado de dos años de una simulación externa,")
    print("  y NO puede compararse directamente con el holdout de 76 señales sin re-ejecutar el detector barra a barra.")
    print("  En modo sombra real (12 eventos observados), el filtro H4 evitó 2 pérdidas (-1.85 R vs -3.33 R de la base).")

    print("\n2. COMPARACIÓN EN TRAIN (226 OPERACIONES IDENTICAS):")
    tr_rows = [
        {'Variante': '1. Base sin filtros', 'Trades': m1_tr['n'], 'Net R': f"{m1_tr['net_r']:+.2f} R", 'WR (%)': f"{m1_tr['wr']:.1f}%", 'PF': m1_tr['pf'], 'MaxDD (R)': m1_tr['max_dd'], 'AUC': '-', 'Brier': '-'},
        {'Variante': '2. Filtro H4 fresco solo', 'Trades': 'N/D*', 'Net R': 'N/D*', 'WR (%)': 'N/D*', 'PF': 'N/D*', 'MaxDD (R)': 'N/D*', 'AUC': '-', 'Brier': '-'},
        {'Variante': '3. LightGBM Actual (0.35)', 'Trades': m3_tr['n'], 'Net R': f"{m3_tr['net_r']:+.2f} R", 'WR (%)': f"{m3_tr['wr']:.1f}%", 'PF': m3_tr['pf'], 'MaxDD (R)': m3_tr['max_dd'], 'AUC': m3_tr['auc'], 'Brier': m3_tr['brier']},
        {'Variante': '4. Modelo Regularizado (0.33)', 'Trades': m4_tr['n'], 'Net R': f"{m4_tr['net_r']:+.2f} R", 'WR (%)': f"{m4_tr['wr']:.1f}%", 'PF': m4_tr['pf'], 'MaxDD (R)': m4_tr['max_dd'], 'AUC': m4_tr['auc'], 'Brier': m4_tr['brier']},
        {'Variante': '5. Modelo Spread Norm Z (0.35, Limpio)', 'Trades': m5_tr['n'], 'Net R': f"{m5_tr['net_r']:+.2f} R", 'WR (%)': f"{m5_tr['wr']:.1f}%", 'PF': m5_tr['pf'], 'MaxDD (R)': m5_tr['max_dd'], 'AUC': m5_tr['auc'], 'Brier': m5_tr['brier']}
    ]
    print(pd.DataFrame(tr_rows).to_string(index=False))

    # -------------------------------------------------------------
    # DESGLOSE POR ACTIVO Y POR CLASE DE ACTIVO EN HOLDOUT
    # -------------------------------------------------------------
    holdout_df['p_act'] = p_ho_actual
    holdout_df['p_reg'] = p_ho_reg
    holdout_df['p_norm'] = p_ho_norm
    
    print("\n3. DESGLOSE POR CLASE DE ACTIVO EN HOLDOUT (SINTÉTICOS VS FINANCIEROS):")
    for is_syn, grp in holdout_df.groupby('is_synthetic'):
        cls_name = "Sintéticos Deriv (12 Activos)" if is_syn == 1.0 else "Activos Financieros (Forex, Oro, W30, BTC)"
        acc3 = grp[grp['p_act'] >= 0.35]
        acc4 = grp[grp['p_reg'] >= 0.33]
        acc5 = grp[grp['p_norm'] >= 0.35]
        print(f"\n[{cls_name}] Total Base: {len(grp)} trades, Net R: {grp['rr'].sum():+.2f} R, WR: {(grp['rr']>0).mean()*100:.1f}%")
        print(f"  * Modelo 3 Actual:       {len(acc3):2d} trades | Net R: {acc3['rr'].sum():+6.2f} R | WR: {(acc3['rr']>0).mean()*100:5.1f}% | PF: {(acc3[acc3.rr>0].rr.sum() / abs(acc3[acc3.rr<0].rr.sum())) if len(acc3[acc3.rr<0])>0 else 999:.3f}")
        print(f"  * Modelo 4 Regularizado: {len(acc4):2d} trades | Net R: {acc4['rr'].sum():+6.2f} R | WR: {(acc4['rr']>0).mean()*100:5.1f}% | PF: {(acc4[acc4.rr>0].rr.sum() / abs(acc4[acc4.rr<0].rr.sum())) if len(acc4[acc4.rr<0])>0 else 999:.3f}")
        print(f"  * Modelo 5 Spread Norm:  {len(acc5):2d} trades | Net R: {acc5['rr'].sum():+6.2f} R | WR: {(acc5['rr']>0).mean()*100:5.1f}% | PF: {(acc5[acc5.rr>0].rr.sum() / abs(acc5[acc5.rr<0].rr.sum())) if len(acc5[acc5.rr<0])>0 else 999:.3f}")

    print("\n4. DESGLOSE INDIVIDUAL POR ACTIVO EN HOLDOUT (76 TRADES):")
    sym_rows = []
    for sym, grp in holdout_df.groupby('symbol'):
        acc3 = grp[grp['p_act'] >= 0.35]
        acc4 = grp[grp['p_reg'] >= 0.33]
        acc5 = grp[grp['p_norm'] >= 0.35]
        sym_rows.append({
            'Activo': sym,
            'Tipo': 'Sintético' if any(k in sym for k in ['Crash', 'Boom', 'Step', 'Jump']) else 'Financiero',
            'Base N': len(grp),
            'Base R': round(grp['rr'].sum(), 2),
            'M3 N': len(acc3),
            'M3 R': round(acc3['rr'].sum(), 2) if len(acc3) > 0 else 0.0,
            'M4 N': len(acc4),
            'M4 R': round(acc4['rr'].sum(), 2) if len(acc4) > 0 else 0.0,
            'M5 N': len(acc5),
            'M5 R': round(acc5['rr'].sum(), 2) if len(acc5) > 0 else 0.0,
        })
    df_sym = pd.DataFrame(sym_rows).sort_values(['Tipo', 'Base N'], ascending=[True, False])
    print(df_sym.to_string(index=False))

if __name__ == '__main__':
    run_fair_comparison()
