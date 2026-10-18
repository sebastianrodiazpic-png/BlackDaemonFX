import pandas as pd
import numpy as np
import lightgbm as lgb
from sklearn.metrics import roc_auc_score, brier_score_loss

df = pd.read_csv('storage/analysis/msnr_v21_two_years_20261011/trades.csv')
enabled_msnr = [
    'Crash 500 Index', 'Crash 600 Index', 'Crash 1000 Index', 'Boom 1000 Index',
    'Boom 500 Index', 'Boom 300 Index', 'Step Index', 'Step Index 400',
    'Wall Street 30', 'XAUUSD', 'EURUSD', 'GBPUSD', 'USDJPY',
    'GBPJPY', 'GBPAUD', 'Jump 10 Index', 'Jump 25 Index', 'Jump 50 Index', 'BTCUSD'
]
v21_en = df[(df['version']=='msnr-v2.1-persistent-retest') & (df['symbol'].isin(enabled_msnr))].sort_values('time').reset_index(drop=True)
v21_en['t_entry'] = pd.to_datetime(v21_en['time'], utc=True)
v21_en['target'] = (v21_en['rr'] > 0).astype(int)

# Features
v21_en['hour'] = v21_en['t_entry'].dt.hour
v21_en['dayofweek'] = v21_en['t_entry'].dt.dayofweek
v21_en['is_synthetic'] = v21_en['symbol'].apply(lambda s: 1.0 if any(k in s for k in ['Crash', 'Boom', 'Step', 'Jump', 'Volatility']) else 0.0)
v21_en['is_buy'] = (v21_en['direction'] == 'BUY').astype(float)
v21_en['spread_ratio'] = v21_en['spread'] / v21_en['risk_atr'].clip(lower=0.0001)
v21_en['risk_atr_norm'] = v21_en['risk_atr'] / v21_en['entry'].clip(lower=0.0001)
v21_en['scen_h4'] = (v21_en['scenario'] == 'h4_continuation').astype(float)
v21_en['scen_v2'] = (v21_en['scenario'] == 'v2_rejection').astype(float)
v21_en['trigger_retest'] = (v21_en['trigger'] == 'retest').astype(float)

split_idx = int(len(v21_en) * 0.75)
train_df = v21_en.iloc[:split_idx].copy()
holdout_df = v21_en.iloc[split_idx:].copy()

# 1. Leakage Version (as in offline_msnr_experiment_framework.py)
v21_leak = v21_en.copy()
v21_leak['spread_ratio_asset_z'] = v21_leak.groupby('symbol')['spread_ratio'].transform(
    lambda x: (x - x.mean()) / (x.std() + 1e-6) if len(x) > 1 else 0.0
)
tr_leak = v21_leak.iloc[:split_idx].copy()
ho_leak = v21_leak.iloc[split_idx:].copy()

# 2. Strict No-Leakage Version (fit strictly on train)
stats = train_df.groupby('symbol')['spread_ratio'].agg(['mean', 'std'])
glob_mean = train_df['spread_ratio'].mean()
glob_std = train_df['spread_ratio'].std() + 1e-6

def get_z(row, stats_df, g_m, g_s):
    sym = row['symbol']
    if sym in stats_df.index and not np.isnan(stats_df.loc[sym, 'std']) and stats_df.loc[sym, 'std'] > 1e-6:
        return (row['spread_ratio'] - stats_df.loc[sym, 'mean']) / stats_df.loc[sym, 'std']
    return (row['spread_ratio'] - g_m) / g_s

train_df['spread_ratio_asset_z'] = train_df.apply(lambda r: get_z(r, stats, glob_mean, glob_std), axis=1)
holdout_df['spread_ratio_asset_z'] = holdout_df.apply(lambda r: get_z(r, stats, glob_mean, glob_std), axis=1)

feats = ['hour', 'dayofweek', 'is_synthetic', 'is_buy', 'spread_ratio_asset_z', 'risk_atr_norm', 'scen_h4', 'scen_v2', 'trigger_retest']

# Model 5 Leakage
m_leak = lgb.LGBMClassifier(n_estimators=40, max_depth=2, num_leaves=4, learning_rate=0.03, min_child_samples=25, reg_alpha=0.5, reg_lambda=1.0, random_state=42, verbosity=-1)
m_leak.fit(tr_leak[feats].values, tr_leak['target'].values)
p_tr_leak = m_leak.predict_proba(tr_leak[feats].values)[:, 1]
p_ho_leak = m_leak.predict_proba(ho_leak[feats].values)[:, 1]

# Model 5 No-Leakage
m_clean = lgb.LGBMClassifier(n_estimators=40, max_depth=2, num_leaves=4, learning_rate=0.03, min_child_samples=25, reg_alpha=0.5, reg_lambda=1.0, random_state=42, verbosity=-1)
m_clean.fit(train_df[feats].values, train_df['target'].values)
p_tr_clean = m_clean.predict_proba(train_df[feats].values)[:, 1]
p_ho_clean = m_clean.predict_proba(holdout_df[feats].values)[:, 1]

print("=== COMPARACIÓN MODELO 5: CON FUGA VS SIN FUGA ===")
print(f"CON FUGA:  Train AUC={roc_auc_score(tr_leak['target'], p_tr_leak):.4f} | Holdout AUC={roc_auc_score(ho_leak['target'], p_ho_leak):.4f} | Holdout Brier={brier_score_loss(ho_leak['target'], p_ho_leak):.4f}")
print(f"SIN FUGA:  Train AUC={roc_auc_score(train_df['target'], p_tr_clean):.4f} | Holdout AUC={roc_auc_score(holdout_df['target'], p_ho_clean):.4f} | Holdout Brier={brier_score_loss(holdout_df['target'], p_ho_clean):.4f}")

acc_leak = p_ho_leak >= 0.35
acc_clean = p_ho_clean >= 0.35
print(f"Holdout con Fuga (th=0.35): Trades={acc_leak.sum()}, Net R={ho_leak.iloc[acc_leak]['rr'].sum():.2f} R, WR={(ho_leak.iloc[acc_leak]['rr']>0).mean()*100:.1f}%")
print(f"Holdout sin Fuga (th=0.35): Trades={acc_clean.sum()}, Net R={holdout_df.iloc[acc_clean]['rr'].sum():.2f} R, WR={(holdout_df.iloc[acc_clean]['rr']>0).mean()*100:.1f}%")
