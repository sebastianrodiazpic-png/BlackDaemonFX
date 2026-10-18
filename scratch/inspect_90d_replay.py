import pandas as pd
from pathlib import Path

p = Path('storage/analysis/replay_malaysian_snr_90d_trades.csv')
if p.exists():
    df = pd.read_csv(p)
    print("=== replay_malaysian_snr_90d_trades.csv ===")
    print("Total trades:", len(df))
    print("Columns:", df.columns.tolist()[:15])
    print("Symbols (count):", len(df['symbol'].unique()))
    print("Symbols list:\n", sorted(df['symbol'].unique()))
else:
    print("File does not exist")
