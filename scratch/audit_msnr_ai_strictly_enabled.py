"""Audit and train AI strictly on the 19 enabled symbols of Malaysian SNR."""
import sys
from pathlib import Path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import pandas as pd
import numpy as np
import lightgbm as lgb
from sklearn.metrics import roc_auc_score, brier_score_loss

def run_msnr_strictly_enabled_ai():
    df = pd.read_csv(PROJECT_ROOT / 'storage/analysis/msnr_v21_two_years_20261011/trades.csv')
    v21 = df[df['version'] == 'msnr-v2.1-persistent-retest'].sort_values('time').reset_index(drop=True)

    enabled_msnr = [
        'Crash 500 Index', 'Crash 600 Index', 'Crash 1000 Index', 'Boom 1000 Index',
        'Boom 500 Index', 'Boom 300 Index', 'Step Index', 'Step Index 400',
        'Wall Street 30', 'XAUUSD', 'EURUSD', 'GBPUSD', 'USDJPY',
        'GBPJPY', 'GBPAUD', 'Jump 10 Index', 'Jump 25 Index', 'Jump 50 Index', 'BTCUSD'
    ]

    v21_en = v21[v21['symbol'].isin(enabled_msnr)].reset_index(drop=True)
    n_total = len(v21_en)
    print(f"Total v21 trades on 19 enabled symbols: {n_total}")
    
    # Chronological Split: 75% Train, 25% Holdout
    split_idx = int(n_total * 0.75) # 226 train, 76 holdout
    train_df = v21_en.iloc[:split_idx].copy()
    holdout_df = v21_en.iloc[split_idx:].copy()
    
    print(f"Train set: {len(train_df)} trades ({train_df.time.iloc[0]} to {train_df.time.iloc[-1]})")
    print(f"Holdout set: {len(holdout_df)} trades ({holdout_df.time.iloc[0]} to {holdout_df.time.iloc[-1]})")
    print(f"Train Base Net R: {train_df['rr'].sum():.2f} R (WR: {(train_df['rr'] > 0).mean()*100:.1f}%)")
    print(f"Holdout Base Net R: {holdout_df['rr'].sum():.2f} R (WR: {(holdout_df['rr'] > 0).mean()*100:.1f}%)")
    
    # Feature Engineering without ANY lookahead
    # Parse time
    for d in [train_df, holdout_df]:
        t = pd.to_datetime(d['time'])
        d['hour'] = t.dt.hour
        d['dayofweek'] = t.dt.dayofweek
        d['is_synthetic'] = d['symbol'].apply(lambda s: 1.0 if any(k in s for k in ['Crash', 'Boom', 'Step', 'Jump', 'Volatility']) else 0.0)
        d['is_buy'] = (d['direction'] == 'BUY').astype(float)
        d['spread_ratio'] = d['spread'] / d['risk_atr'].clip(lower=0.0001)
        d['risk_atr_norm'] = d['risk_atr'] / d['entry'].clip(lower=0.0001)
        # One-hot scenario if available
        d['scen_h4'] = (d['scenario'] == 'h4_continuation').astype(float)
        d['scen_v2'] = (d['scenario'] == 'v2_rejection').astype(float)
        d['trigger_retest'] = (d['trigger'] == 'retest').astype(float)
        # Target: binary win
        d['target'] = (d['rr'] > 0).astype(int)

    feature_cols = [
        'hour', 'dayofweek', 'is_synthetic', 'is_buy', 'spread_ratio',
        'risk_atr_norm', 'scen_h4', 'scen_v2', 'trigger_retest'
    ]
    
    X_train = train_df[feature_cols].values
    y_train = train_df['target'].values
    X_holdout = holdout_df[feature_cols].values
    y_holdout = holdout_df['target'].values
    
    # Train LightGBM model
    model = lgb.LGBMClassifier(
        n_estimators=60,
        max_depth=3,
        num_leaves=7,
        learning_rate=0.05,
        min_child_samples=10,
        random_state=42,
        verbosity=-1
    )
    model.fit(X_train, y_train)
    
    train_probs = model.predict_proba(X_train)[:, 1]
    holdout_probs = model.predict_proba(X_holdout)[:, 1]
    
    auc_train = roc_auc_score(y_train, train_probs) if len(np.unique(y_train)) > 1 else 0.5
    auc_holdout = roc_auc_score(y_holdout, holdout_probs) if len(np.unique(y_holdout)) > 1 else 0.5
    brier_holdout = brier_score_loss(y_holdout, holdout_probs)
    
    print(f"\nModel Performance:")
    print(f"Train AUC: {auc_train:.4f}")
    print(f"Holdout AUC: {auc_holdout:.4f}")
    print(f"Holdout Brier Score: {brier_holdout:.4f}")
    
    # Sweep threshold on TRAIN to find optimal threshold, then evaluate on HOLDOUT
    print(f"\nThreshold Sweep on Train vs Frozen Holdout Evaluation:")
    best_th = 0.50
    best_train_net = -999.0
    for th in [0.30, 0.35, 0.40, 0.45, 0.50, 0.55]:
        tr_acc = train_probs >= th
        n_tr = tr_acc.sum()
        tr_net = train_df.iloc[tr_acc]['rr'].sum() if n_tr > 0 else 0.0
        if tr_net > best_train_net and n_tr >= 20:
            best_train_net = tr_net
            best_th = th
            
        ho_acc = holdout_probs >= th
        n_ho = ho_acc.sum()
        ho_net = holdout_df.iloc[ho_acc]['rr'].sum() if n_ho > 0 else 0.0
        ho_wr = (holdout_df.iloc[ho_acc]['rr'] > 0).mean() * 100 if n_ho > 0 else 0.0
        print(f"  Th = {th:.2f} | Train Acc = {n_tr:3d}/{len(train_df)} ({tr_net:+6.2f} R) | Holdout Acc = {n_ho:2d}/{len(holdout_df)} ({ho_net:+6.2f} R, WR: {ho_wr:5.1f}%)")
        
    print(f"\nOptimal Train Selected Threshold: {best_th:.2f}")
    # Frozen evaluation on holdout with best_th
    final_ho_acc = holdout_probs >= best_th
    final_ho_trades = holdout_df.iloc[final_ho_acc]
    n_final = len(final_ho_trades)
    net_final = final_ho_trades['rr'].sum() if n_final > 0 else 0.0
    wr_final = (final_ho_trades['rr'] > 0).mean() * 100 if n_final > 0 else 0.0
    gross_w = final_ho_trades[final_ho_trades['rr'] > 0]['rr'].sum() if n_final > 0 else 0.0
    gross_l = abs(final_ho_trades[final_ho_trades['rr'] < 0]['rr'].sum()) if n_final > 0 else 0.0
    pf_final = gross_w / gross_l if gross_l > 0 else float('inf')
    
    print(f"FINAL HOLDOUT RESULT (Strictly 19 Enabled Symbols, Frozen Th={best_th:.2f}):")
    print(f"Accepted Trades: {n_final} / {len(holdout_df)} ({n_final/len(holdout_df)*100:.1f}%)")
    print(f"Net R: {net_final:+6.2f} R")
    print(f"Win Rate: {wr_final:.1f}%")
    print(f"Profit Factor: {pf_final:.3f}")

if __name__ == '__main__':
    run_msnr_strictly_enabled_ai()
