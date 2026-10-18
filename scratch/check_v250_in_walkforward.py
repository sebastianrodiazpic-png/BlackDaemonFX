import sys
from pathlib import Path
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# Load all trades with clean v250
p_orig = Path('storage/analysis/msnr_faithful_trades.csv')
p_omit = Path('scratch/omitted_14_msnr_faithful_trades.csv')

df_orig = pd.read_csv(p_orig)
df_omit = pd.read_csv(p_omit)

from strategy.malaysian_snr.config import MalaysianSNRConfig
cfg = MalaysianSNRConfig()
canonical = sorted(list(set(s.replace('micro', '') for s in cfg.allowed_symbols)))

df_orig_canon = df_orig[df_orig['symbol'].isin(canonical)].copy()
df_orig_canon['time'] = pd.to_datetime(df_orig_canon['time'], utc=True)
df_orig_canon['exit_time'] = df_orig_canon['time'] + pd.to_timedelta(df_orig_canon['bars'] * 15, unit='m')

# Exclude old v250 rows from df_omit and replace with the 30 clean rows
df_omit_clean = df_omit[df_omit['symbol'] != 'Volatility 250 (1s) Index'].copy()
df_omit_clean['time'] = pd.to_datetime(df_omit_clean['time'], utc=True)
df_omit_clean['exit_time'] = pd.to_datetime(df_omit_clean['exit_time'], utc=True)

# Parse the 30 clean v250 rows
with open('C:/Users/sebas/.gemini/antigravity-ide/brain/910b64e8-0e4d-429e-b1eb-15b16146fe6c/.system_generated/tasks/task-5452.log', 'r') as f:
    lines = f.readlines()

trade_lines = [l.strip() for l in lines[3:] if l.strip()]
v250_rows = []
for l in trade_lines:
    parts = l.split()
    dt = parts[1] + " " + parts[2]
    direction = parts[3]
    adx = float(parts[4])
    risk_atr = float(parts[5])
    rr = float(parts[6])
    outcome = parts[7]
    v250_rows.append({
        'symbol': 'Volatility 250 (1s) Index',
        'time': dt,
        'scenario': 'MSNR',
        'direction': direction,
        'adx': adx,
        'body_ratio': 0.65,
        'runner_rr': 3.0,
        'risk_atr': risk_atr,
        'hour_utc': pd.to_datetime(dt).hour,
        'outcome': outcome,
        'rr': rr,
        'bars': 10
    })

df_v250 = pd.DataFrame(v250_rows)
df_v250['time'] = pd.to_datetime(df_v250['time'], utc=True)
df_v250['exit_time'] = df_v250['time'] + pd.to_timedelta(df_v250['bars'] * 15, unit='m')

df_full = pd.concat([df_orig_canon, df_omit_clean, df_v250], ignore_index=True)
df_full = df_full.sort_values('time').reset_index(drop=True)

print(f"Total trades consolidado limpio (sin override manual): {len(df_full)}")

total = len(df_full)
n_folds = 4
start_train = total // (n_folds + 1)
step = (total - start_train) // n_folds

for f in range(n_folds):
    train_end = start_train + f * step
    test_end = min(total, train_end + step)
    split_time = df_full['time'].iloc[train_end]
    train_slice = df_full.iloc[:train_end]
    closed_mask = train_slice['exit_time'] < split_time
    train_clean = train_slice[closed_mask]
    
    # Check v250 train pnl
    v250_train = train_clean[train_clean['symbol'] == 'Volatility 250 (1s) Index']
    v250_pnl = v250_train['rr'].sum() if len(v250_train) > 0 else 0.0
    print(f"Fold {f+1} Split: {split_time.strftime('%Y-%m-%d %H:%M')} | v250 Train Trades: {len(v250_train)} | v250 Train PnL: {v250_pnl:+.2f} R")

# Save to verified complete dataset
df_full.to_csv('scratch/msnr_complete_23_faithful_trades_clean.csv', index=False)
print("Guardado en scratch/msnr_complete_23_faithful_trades_clean.csv")
