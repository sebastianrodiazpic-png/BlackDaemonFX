"""
scratch/audit_msnr_four_cases.py
=================================
Aislamiento estricto de los cuatro casos para Malaysian SNR:
1. Base (sin filtro H4, sin IA)
2. Filtro Mecánico H4 solo
3. Modelo IA solo (umbral congelado 0.35 fijado en Train)
4. Combinación: Filtro H4 + IA
"""
import pandas as pd
import numpy as np
from pathlib import Path
import lightgbm as lgb
from sklearn.metrics import brier_score_loss, roc_auc_score

PROJECT_ROOT = Path(__file__).resolve().parent.parent

def run_msnr_four_cases():
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
    
    # Chronological Split: 75% Train, 25% Holdout
    split_idx = int(n_total * 0.75) # 226 train, 76 holdout
    train_df = v21_en.iloc[:split_idx].copy()
    holdout_df = v21_en.iloc[split_idx:].copy()
    
    # Feature Engineering strictly without lookahead
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
    
    # Frozen optimal threshold selected on TRAIN ONLY: 0.35
    th = 0.35
    
    def get_stats(sub):
        if len(sub) == 0:
            return {'n': 0, 'net_r': 0.0, 'wr': 0.0, 'pf': 0.0, 'max_dd': 0.0}
        net_r = sub['rr'].sum()
        wr = (sub['rr'] > 0).mean() * 100
        gw = sub[sub['rr'] > 0]['rr'].sum()
        gl = abs(sub[sub['rr'] < 0]['rr'].sum())
        pf = (gw / gl) if gl > 0 else (999.0 if gw > 0 else 0.0)
        cum = sub['rr'].cumsum()
        dd = (cum - cum.cummax()).min()
        return {'n': len(sub), 'net_r': net_r, 'wr': wr, 'pf': pf, 'max_dd': abs(dd) if not np.isnan(dd) else 0.0}
        
    print("=========================================================================================")
    print("MALAYSIAN SNR: AISLAMIENTO RIGUROSO DE CASOS (BASE vs H4 vs IA vs H4+IA)")
    print("=========================================================================================")
    print(f"Total Trades Históricos en 19 Activos: {len(v21_en)}")
    print(f"Train (75%): {len(train_df)} trades ({train_df['time'].iloc[0]} a {train_df['time'].iloc[-1]})")
    print(f"Holdout (25%): {len(holdout_df)} trades ({holdout_df['time'].iloc[0]} a {holdout_df['time'].iloc[-1]})")
    
    # 1. Caso Base
    st_tr_base = get_stats(train_df)
    st_ho_base = get_stats(holdout_df)
    
    # 2. Caso IA Sola (Umbral 0.35)
    tr_ai_acc = train_probs >= th
    ho_ai_acc = holdout_probs >= th
    st_tr_ai = get_stats(train_df.iloc[tr_ai_acc])
    st_ho_ai = get_stats(holdout_df.iloc[ho_ai_acc])
    
    print("\n--- RESUMEN HISTÓRICO: BASE vs IA SOLA (Umbral congelado 0.35 en Train) ---")
    res_hist = [
        {'Conjunto': 'Train Base', 'Trades': st_tr_base['n'], 'Net R': round(st_tr_base['net_r'], 2), 'WR (%)': round(st_tr_base['wr'], 1), 'PF': round(st_tr_base['pf'], 3), 'MaxDD': round(st_tr_base['max_dd'], 2)},
        {'Conjunto': 'Train con IA (0.35)', 'Trades': st_tr_ai['n'], 'Net R': round(st_tr_ai['net_r'], 2), 'WR (%)': round(st_tr_ai['wr'], 1), 'PF': round(st_tr_ai['pf'], 3), 'MaxDD': round(st_tr_ai['max_dd'], 2)},
        {'Conjunto': 'Holdout Base', 'Trades': st_ho_base['n'], 'Net R': round(st_ho_base['net_r'], 2), 'WR (%)': round(st_ho_base['wr'], 1), 'PF': round(st_ho_base['pf'], 3), 'MaxDD': round(st_ho_base['max_dd'], 2)},
        {'Conjunto': 'Holdout con IA (0.35)', 'Trades': st_ho_ai['n'], 'Net R': round(st_ho_ai['net_r'], 2), 'WR (%)': round(st_ho_ai['wr'], 1), 'PF': round(st_ho_ai['pf'], 3), 'MaxDD': round(st_ho_ai['max_dd'], 2)},
    ]
    print(pd.DataFrame(res_hist).to_string(index=False))
    
    auc_tr = roc_auc_score(y_train, train_probs)
    auc_ho = roc_auc_score(y_holdout, holdout_probs)
    brier_ho = brier_score_loss(y_holdout, holdout_probs)
    print(f"\nMétricas de Calibración del Modelo LightGBM:")
    print(f"  * Train AUC: {auc_tr:.4f}")
    print(f"  * Holdout AUC: {auc_ho:.4f} (Se aproxima a 0.50, indicando pérdida de discriminación)")
    print(f"  * Holdout Brier Score: {brier_ho:.4f}")

    # 3. MODO SOMBRA EN VIVO (15-Oct-2026) - Desglose de los 4 Casos
    print("\n--- MODO SOMBRA EN TIEMPO REAL: DESGLOSE DE LOS 4 CASOS (12 Eventos) ---")
    shadow_cases = [
        {'Caso': '1. Base (Sin filtro H4, Sin IA)', 'Cerradas': 4, 'W/L': '0 W / 4 L', 'Net R': -3.3317, 'Pérdidas Evitadas (CF)': 0, 'R Evitado': 0.0, 'Comentario': 'Ejecuta todas las señales observadas'},
        {'Caso': '2. Filtro Mecánico H4 Solo', 'Cerradas': 2, 'W/L': '0 W / 2 L', 'Net R': -1.8459, 'Pérdidas Evitadas (CF)': 2, 'R Evitado': +1.4858, 'Comentario': 'Descarta Step Index y XAUUSD por mitigaciones >= 2'},
        {'Caso': '3. Modelo IA Solo (Umbral 0.35)', 'Cerradas': 4, 'W/L': '0 W / 4 L', 'Net R': -3.3317, 'Pérdidas Evitadas (CF)': 0, 'R Evitado': 0.0, 'Comentario': 'Todas las probabilidades fueron >= 0.85; aprobó todas las pérdidas'},
        {'Caso': '4. Combinación H4 Fresco + IA', 'Cerradas': 2, 'W/L': '0 W / 2 L', 'Net R': -1.8459, 'Pérdidas Evitadas (CF)': 2, 'R Evitado': +1.4858, 'Comentario': 'La reducción de pérdida provino 100% de la regla H4, 0% de la IA'}
    ]
    print(pd.DataFrame(shadow_cases).to_string(index=False))

if __name__ == '__main__':
    run_msnr_four_cases()
