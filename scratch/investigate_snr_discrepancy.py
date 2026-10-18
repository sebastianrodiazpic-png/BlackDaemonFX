import sys
from pathlib import Path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import pandas as pd
import numpy as np
from config.strategy_config import PRUNED_ASSET_UNIVERSE
from strategy.malaysian_snr.config import MalaysianSNRConfig

def compute_metrics(rr_series: pd.Series) -> dict:
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

df_msnr = pd.read_csv('storage/analysis/msnr_faithful_trades.csv')
allowed = MalaysianSNRConfig.allowed_symbols
df_allowed = df_msnr[df_msnr['symbol'].isin(allowed)].copy()

print(f"Total rows in df_msnr: {len(df_msnr)}")
print(f"Total rows in df_allowed: {len(df_allowed)}")
print("Scenario value counts in df_allowed:")
print(df_allowed['scenario'].value_counts())

# 1. Base
m_base = compute_metrics(df_allowed['rr'])
print("\n1. Base df_allowed:")
print(m_base)

# 2. No ESC 1
m_no_esc1 = compute_metrics(df_allowed[df_allowed['scenario'] != 'ESC_1_CONTINUATION']['rr'])
print("\n2. df_allowed[scenario != ESC_1_CONTINUATION]:")
print(m_no_esc1)

# Test combinations of filters on df_allowed:
df_allowed['time'] = pd.to_datetime(df_allowed['time'], utc=True)
df_sorted = df_allowed.sort_values('time').reset_index(drop=True)

print("\n--- SEARCHING FOR 599 TRADES AND +6.19 R IN REPLAY ---")
for sym in df_sorted['symbol'].unique():
    sub = df_sorted[(df_sorted['scenario'] != 'ESC_1_CONTINUATION') & (df_sorted['symbol'] != sym)]
    if len(sub) == 599:
        print(f"Match excluding {sym}: len={len(sub)}, net_r={sub['rr'].sum():.2f}R")

# What about exclusions of 2 assets?
symbols = list(df_sorted['symbol'].unique())
for i in range(len(symbols)):
    for j in range(i+1, len(symbols)):
        sub = df_sorted[(df_sorted['scenario'] != 'ESC_1_CONTINUATION') & (~df_sorted['symbol'].isin([symbols[i], symbols[j]]))]
        if len(sub) == 599:
            print(f"Match excluding {symbols[i]} and {symbols[j]}: len={len(sub)}, net_r={sub['rr'].sum():.2f}R")

# What about on the full df_msnr (1368 rows)?
for sym in df_msnr['symbol'].unique():
    sub = df_msnr[(df_msnr['scenario'] != 'ESC_1_CONTINUATION') & (df_msnr['symbol'] != sym)]
    if len(sub) == 599:
        print(f"Match in full df excluding {sym}: len={len(sub)}, net_r={sub['rr'].sum():.2f}R")

# What about body_ratio, adx, rollover in df_sorted?
for b in [0.0, 0.35, 0.40, 0.45, 0.50]:
    for a in [0.0, 15.0, 20.0, 25.0]:
        sub = df_sorted[(df_sorted['scenario'] != 'ESC_1_CONTINUATION') & (df_sorted['body_ratio'] >= b) & (df_sorted['adx'] >= a)]
        if len(sub) == 599 or abs(sub['rr'].sum() - 6.19) < 0.1:
            print(f"Match body>={b}, adx>={a}: len={len(sub)}, net_r={sub['rr'].sum():.2f}R")

# What about in Holdout: searching for 239 trades and -14.33 R?
split_idx = int(len(df_sorted) * 0.60)
test_sorted = df_sorted.iloc[split_idx:].copy()
print("\n--- SEARCHING FOR -14.33 R IN HOLDOUT ---")
for sym in test_sorted['symbol'].unique():
    sub = test_sorted[(test_sorted['scenario'] != 'ESC_1_CONTINUATION') & (test_sorted['symbol'] != sym)]
    if abs(sub['rr'].sum() - (-14.33)) < 0.2:
        print(f"Holdout match excluding {sym}: len={len(sub)}, net_r={sub['rr'].sum():.2f}R")

for b in [0.0, 0.35, 0.40, 0.45, 0.50]:
    for a in [0.0, 15.0, 20.0, 25.0]:
        sub = test_sorted[(test_sorted['scenario'] != 'ESC_1_CONTINUATION') & (test_sorted['body_ratio'] >= b) & (test_sorted['adx'] >= a)]
        if abs(sub['rr'].sum() - (-14.33)) < 0.2:
            print(f"Holdout match body>={b}, adx>={a}: len={len(sub)}, net_r={sub['rr'].sum():.2f}R")


# Where does 599 come from?
# Could 599 be ICT? Let's check ICT!
df_ict = pd.read_csv('storage/analysis/ict_faithful_trades.csv')
ict_canonical = sorted(list(set(s.replace('micro', '') for s in PRUNED_ASSET_UNIVERSE['ICT'])))
df_ict_en = df_ict[df_ict['symbol'].isin(ict_canonical)].copy()
print(f"\nTotal ICT canonical rows: {len(df_ict_en)}")
# What about ICT excluding Jump 25?
print("ICT excluding Jump 25:", compute_metrics(df_ict_en[df_ict_en['symbol'] != 'Jump 25 Index']['rr']))
# What about ICT excluding deadzones (0, 6, 20, 22)?
print("ICT excluding deadzones (0,6,20,22):", compute_metrics(df_ict_en[~df_ict_en['ny_hour'].isin([0, 6, 20, 22])]['rr']))
# In the earlier report table for ICT:
# "3. Filtro Horas Tóxicas Solo (0,6,20,22) | 596 | 33,72 % | -3,70 R"
# "4. Poda Jump 25 Solo | 549 | 34,43 % | +8,20 R"

# Now let's check holdout of Malaysian SNR:
split_idx = int(len(df_allowed) * 0.60)
train_snr = df_allowed.iloc[:split_idx].copy()
test_snr = df_allowed.iloc[split_idx:].copy()

print(f"\nTrain SNR rows: {len(train_snr)}, Test SNR rows: {len(test_snr)}")
print("Train scenario counts:")
print(train_snr['scenario'].value_counts())
print("Test scenario counts:")
print(test_snr['scenario'].value_counts())

print("\nTrain PnL by scenario:")
print(train_snr.groupby('scenario')['rr'].agg(trades='count', net_r='sum', mean_r='mean'))

print("\nTest PnL by scenario:")
print(test_snr.groupby('scenario')['rr'].agg(trades='count', net_r='sum', mean_r='mean'))

# Test Base
print("\nTest Base:", compute_metrics(test_snr['rr']))
# Test No Esc1
print("Test No Esc1:", compute_metrics(test_snr[test_snr['scenario'] != 'ESC_1_CONTINUATION']['rr']))
# Test Only Esc3 Fractal
print("Test Only Fractal:", compute_metrics(test_snr[test_snr['scenario'] == 'ESC_3_FRACTAL']['rr']))
# Test Esc3 Fractal + Quasimodo (no continuation)
print("Test Fractal + QM:", compute_metrics(test_snr[test_snr['scenario'].isin(['ESC_3_FRACTAL', 'ESC_3_QUASIMODO'])]['rr']))

