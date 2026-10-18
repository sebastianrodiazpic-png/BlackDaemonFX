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

print("=================================================================")
print("INDEPENDENT CHRONOLOGICAL HOLDOUT AUDIT (ZERO THRESHOLD SNOOPING)")
print("=================================================================")

def run_independent_holdout_audit(strategy_name: str, csv_path: str, r_col_name: str, test_ratio: float = 0.25):
    df = pd.read_csv(csv_path)
    time_col = [c for c in df.columns if 'time' in c.lower() or 'date' in c.lower()][0]
    df['entry_time'] = pd.to_datetime(df[time_col], utc=True)
    if 'exit_time' in df.columns:
        df['exit_time'] = pd.to_datetime(df['exit_time'], utc=True, errors='coerce')
    df = df.sort_values('entry_time').reset_index(drop=True)
    df['realized_r'] = pd.to_numeric(df[r_col_name], errors='coerce').fillna(0.0)
    df['label'] = triple_barrier_label(df['realized_r'], target_tp_r=0.8)

    # Exclude lookahead and realized outcome columns
    leakage_keywords = [
        'outcome', 'exit', 'rr', 'bars', 'pnl', 'profit', 'target', 'result',
        'label', 'realized_r', 'id', 'ticket', 'entry_time', 'time', 'date',
        'leg1', 'leg2', 'reason', 'closed', 'net_r', 'total_r'
    ]
    feature_cols = []
    for col in df.columns:
        if col == r_col_name or any(leak in col.lower() for leak in leakage_keywords):
            continue
        if pd.api.types.is_numeric_dtype(df[col]):
            feature_cols.append(col)
        elif pd.api.types.is_bool_dtype(df[col]):
            df[col] = df[col].astype(int)
            feature_cols.append(col)
        elif df[col].nunique() < 20:
            dummies = pd.get_dummies(df[col], prefix=col, drop_first=True)
            for d in dummies.columns:
                df[d] = dummies[d].astype(int)
                feature_cols.append(d)

    n_samples = len(df)
    split_point = int(n_samples * (1.0 - test_ratio))

    df_dev = df.iloc[:split_point].copy().reset_index(drop=True)
    df_test_holdout = df.iloc[split_point:].copy().reset_index(drop=True)

    dev_start = df_dev['entry_time'].iloc[0].strftime("%Y-%m-%d")
    dev_end = df_dev['entry_time'].iloc[-1].strftime("%Y-%m-%d")
    test_start = df_test_holdout['entry_time'].iloc[0].strftime("%Y-%m-%d")
    test_end = df_test_holdout['entry_time'].iloc[-1].strftime("%Y-%m-%d")

    print(f"\n--- Strategy: {strategy_name} ---")
    print(f"Total Trades: {n_samples}")
    print(f"Development Set (Train/Val): {len(df_dev)} trades | {dev_start} to {dev_end}")
    print(f"Untouched Holdout Test Set: {len(df_test_holdout)} trades | {test_start} to {test_end}")

    # 1. Inside Development Set: Cross-Validation to select optimal threshold
    X_dev = np.clip(df_dev[feature_cols].replace([np.inf, -np.inf], np.nan).fillna(0.0).values.astype(float), -1e7, 1e7)
    y_dev = df_dev['label'].values
    r_dev = df_dev['realized_r'].values

    cv = PurgedGroupTimeSeriesSplit(n_splits=4, embargo_pct=0.01)
    oos_dev_preds = np.zeros(len(df_dev))
    oos_dev_mask = np.zeros(len(df_dev), dtype=bool)

    for tr_idx, val_idx in cv.split(df_dev):
        X_tr, y_tr = X_dev[tr_idx], y_dev[tr_idx]
        X_val, y_val = X_dev[val_idx], y_dev[val_idx]
        if len(np.unique(y_tr)) < 2: continue
        
        gbdt = CalibratedGBDTModel(worker=strategy_name, strategy_name=strategy_name)
        gbdt.fit(X_tr, y_tr, n_estimators=50, max_depth=3, learning_rate=0.04)
        oos_dev_preds[val_idx] = gbdt.predict_proba(X_val)
        oos_dev_mask[val_idx] = True

    valid_dev_idx = np.where(oos_dev_mask)[0]
    best_th = 0.50
    best_expectancy = -999.0

    print("\nThreshold Selection ONLY on Development CV (Test set is untouched):")
    for th in [0.30, 0.35, 0.40, 0.45, 0.50]:
        perf = evaluate_model_performance(y_dev[valid_dev_idx], oos_dev_preds[valid_dev_idx], r_dev[valid_dev_idx], threshold=th)
        print(f"  Th: {th:.2f} | Accepted: {perf['trades_accepted']:4d} | Exp: {perf['expectancy_r']:7.4f}R | PF: {perf['profit_factor']:5.3f} | Net: {perf['net_r']:6.2f}R")
        if perf['trades_accepted'] >= 40 and perf['expectancy_r'] > best_expectancy:
            best_expectancy = perf['expectancy_r']
            best_th = th

    print(f"\n=> Selected Threshold from Dev CV: {best_th:.2f} (frozen for final test)")

    # 2. Train Model on 100% of Development Set
    final_model = CalibratedGBDTModel(worker=strategy_name, strategy_name=strategy_name)
    final_model.fit(X_dev, y_dev, n_estimators=60, max_depth=3, learning_rate=0.04)

    # 3. Evaluate ONCE on Untouched Final Holdout Test Set
    X_test = np.clip(df_test_holdout[feature_cols].replace([np.inf, -np.inf], np.nan).fillna(0.0).values.astype(float), -1e7, 1e7)
    y_test = df_test_holdout['label'].values
    r_test = df_test_holdout['realized_r'].values

    proba_test = final_model.predict_proba(X_test)

    # Baseline Naive on Holdout
    perf_naive = evaluate_model_performance(y_test, np.ones_like(y_test), r_test, threshold=0.0)
    # AI Model with Frozen Threshold on Holdout
    perf_ai = evaluate_model_performance(y_test, proba_test, r_test, threshold=best_th)

    print("\n=================================================================")
    print(f"FINAL INDEPENDENT HOLDOUT RESULTS ({test_start} to {test_end}):")
    print("=================================================================")
    print("Baseline Naive (Sin IA):")
    print(f"  Trades: {perf_naive['trades_total']} | WinRate: {perf_naive['win_rate']*100:.2f}% | Net R: {perf_naive['net_r']:.2f}R | Expectancy: {perf_naive['expectancy_r']:.4f}R | PF: {perf_naive['profit_factor']:.3f} | MaxDD: {perf_naive['max_drawdown_r']:.2f}R")
    print(f"AI LightGBM (Umbral Congelado {best_th:.2f}):")
    print(f"  Accepted: {perf_ai['trades_accepted']}/{perf_ai['trades_total']} ({perf_ai['retention_rate']*100:.1f}%) | WinRate: {perf_ai['win_rate']*100:.2f}% | Net R: {perf_ai['net_r']:.2f}R | Expectancy: {perf_ai['expectancy_r']:.4f}R | PF: {perf_ai['profit_factor']:.3f} | MaxDD: {perf_ai['max_drawdown_r']:.2f}R | AUC: {perf_ai['auc_roc']:.4f}")

run_independent_holdout_audit("ICT", "storage/analysis/ict_faithful_trades.csv", "rr", test_ratio=0.25)
