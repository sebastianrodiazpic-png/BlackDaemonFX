import sys
from pathlib import Path
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

p_orig = 'storage/analysis/msnr_faithful_trades.csv'
p_full = 'scratch/msnr_complete_23_faithful_trades.csv'

for name, p in [("ORIG (727 rows)", p_orig), ("FULL 23 (942 rows)", p_full)]:
    df = pd.read_csv(p)
    df['time'] = pd.to_datetime(df['time'], utc=True)
    if 'exit_time' not in df.columns:
        df['exit_time'] = df['time'] + pd.to_timedelta(df['bars'] * 15, unit='m')
    else:
        df['exit_time'] = pd.to_datetime(df['exit_time'], utc=True)
    df = df.sort_values('time').reset_index(drop=True)
    from strategy.malaysian_snr.config import MalaysianSNRConfig
    cfg = MalaysianSNRConfig()
    allowed = set(s.replace('micro', '') for s in cfg.allowed_symbols)
    df = df[df['symbol'].isin(allowed)].reset_index(drop=True)

    total = len(df)
    n_folds = 4
    start_train = total // (n_folds + 1)
    step = (total - start_train) // n_folds

    print(f"\n=== {name} | Total: {total} | start_train: {start_train} | step: {step} ===")
    for f in range(n_folds):
        train_end = start_train + f * step
        test_end = min(total, train_end + step)
        split_time = df['time'].iloc[train_end]
        train_slice = df.iloc[:train_end]
        closed_mask = train_slice['exit_time'] < split_time
        train_clean = train_slice[closed_mask]
        test_slice = df.iloc[train_end:test_end].copy().reset_index(drop=True)

        sym_pnl = train_clean.groupby('symbol')['rr'].sum()
        pos_syms = set(sym_pnl[sym_pnl > 0].index)

        test_causal = test_slice[test_slice['symbol'].isin(pos_syms)]
        v2 = test_causal[(test_causal['adx'] >= 30.0) & (test_causal['risk_atr'] <= 1.5)]
        print(f"  Fold {f+1}: Split={split_time.strftime('%Y-%m-%d %H:%M')} | Pos syms ({len(pos_syms)}): {sorted(pos_syms)} | V2 trades: {len(v2)}")
