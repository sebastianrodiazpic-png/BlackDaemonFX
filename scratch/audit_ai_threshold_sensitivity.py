import pandas as pd
import numpy as np
import json
from pathlib import Path
import sys

ROOT = Path("c:/TradingBoot/smc_synthetic_bot")
sys.path.insert(0, str(ROOT))

from tools.train_unified_multistrategy_ai import (
    PurgedGroupTimeSeriesSplit,
    triple_barrier_label,
    evaluate_model_performance
)
from strategy.ai.gbdt_model import CalibratedGBDTModel, LIGHTGBM_AVAILABLE

# Test threshold sensitivity for ICT
df_ict = pd.read_csv('storage/analysis/ict_faithful_trades.csv')
time_col = [c for c in df_ict.columns if 'time' in c.lower() or 'date' in c.lower()][0]
df_ict['entry_time'] = pd.to_datetime(df_ict[time_col], utc=True)
df_ict = df_ict.sort_values('entry_time').reset_index(drop=True)
df_ict['realized_r'] = pd.to_numeric(df_ict['rr'], errors='coerce').fillna(0.0)
df_ict['label'] = triple_barrier_label(df_ict['realized_r'], target_tp_r=0.8)

# Exclude lookahead
leakage_keywords = ['outcome', 'exit', 'rr', 'bars', 'pnl', 'profit', 'target', 'result', 'label', 'realized_r', 'id', 'ticket', 'entry_time', 'time', 'date']
feature_cols = []
for col in df_ict.columns:
    if col == 'rr' or any(leak in col.lower() for leak in leakage_keywords):
        continue
    if pd.api.types.is_numeric_dtype(df_ict[col]):
        feature_cols.append(col)
    elif pd.api.types.is_bool_dtype(df_ict[col]):
        df_ict[col] = df_ict[col].astype(int)
        feature_cols.append(col)
    elif df_ict[col].nunique() < 20:
        dummies = pd.get_dummies(df_ict[col], prefix=col, drop_first=True)
        for d in dummies.columns:
            df_ict[d] = dummies[d].astype(int)
            feature_cols.append(d)

X = df_ict[feature_cols].values
y = df_ict['label'].values
r = df_ict['realized_r'].values

cv = PurgedGroupTimeSeriesSplit(n_splits=5, embargo_pct=0.01)
oos_preds = np.zeros(len(df_ict))
oos_mask = np.zeros(len(df_ict), dtype=bool)

for train_idx, test_idx in cv.split(df_ict):
    X_tr, y_tr = X[train_idx], y[train_idx]
    X_te, y_te = X[test_idx], y[test_idx]
    if len(np.unique(y_tr)) < 2: continue
    
    gbdt = CalibratedGBDTModel(worker="ICT", strategy_name="ICT")
    gbdt.fit(X_tr, y_tr, n_estimators=60, max_depth=3, learning_rate=0.04)
    oos_preds[test_idx] = gbdt.predict_proba(X_te)
    oos_mask[test_idx] = True

valid_idx = np.where(oos_mask)[0]
y_val = y[valid_idx]
r_val = r[valid_idx]
preds_val = oos_preds[valid_idx]

print("=================================================================")
print("ICT LIGHTGBM THRESHOLD SENSITIVITY & STATISTICAL SAMPLE AUDIT")
print("=================================================================")
print(f"Total OOS Candidates: {len(valid_idx)} trades")
print(f"{'Threshold':10s} | {'Trades':7s} | {'Retention':10s} | {'WinRate':8s} | {'Net R':8s} | {'Expectancy':10s} | {'PF':6s} | {'MaxDD':8s} | {'Sample >= 100?'}")
print("-" * 95)

thresholds = [0.20, 0.25, 0.30, 0.35, 0.40, 0.45, 0.50, 0.55]
for th in thresholds:
    perf = evaluate_model_performance(y_val, preds_val, r_val, threshold=th)
    n_trades = perf['trades_accepted']
    sample_ok = "YES (>=100)" if n_trades >= 100 else "NO (<100)"
    print(f"{th:10.2f} | {n_trades:7d} | {perf['retention_rate']*100:9.1f}% | {perf['win_rate']*100:7.2f}% | {perf['net_r']:8.2f} | {perf['expectancy_r']:10.4f} | {perf['profit_factor']:6.3f} | {perf['max_drawdown_r']:8.2f} | {sample_ok}")
