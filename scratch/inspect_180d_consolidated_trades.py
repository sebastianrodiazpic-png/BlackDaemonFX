import pandas as pd
from pathlib import Path

p1 = Path('storage/analysis/replay_boom_crash_forex_gold_180d_trades.csv')
p2 = Path('storage/analysis/replay_step_vol_jump_180d_trades.csv')

if p1.exists():
    df1 = pd.read_csv(p1)
    print("=== replay_boom_crash_forex_gold_180d_trades.csv ===")
    print("Total rows:", len(df1))
    print("Columns:", df1.columns.tolist())
    print("Symbols:", df1['symbol'].unique() if 'symbol' in df1.columns else "No symbol col")

if p2.exists():
    df2 = pd.read_csv(p2)
    print("\n=== replay_step_vol_jump_180d_trades.csv ===")
    print("Total rows:", len(df2))
    print("Columns:", df2.columns.tolist())
    print("Symbols:", df2['symbol'].unique() if 'symbol' in df2.columns else "No symbol col")
