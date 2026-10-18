import pandas as pd
from pathlib import Path

p_90 = Path('storage/analysis/replay_malaysian_snr_90d_trades.csv')
p_2y = Path('storage/analysis/replay_malaysian_snr_2y_trades.csv')

for p, name in [(p_90, "90d"), (p_2y, "2y")]:
    if p.exists():
        df = pd.read_csv(p)
        print(f"=== {p.name} ({name}) ===")
        print("Total trades:", len(df))
        print("Columns:", df.columns.tolist()[:15])
        print("Unique symbols:", len(df['symbol'].unique()))
        has_adx = 'adx' in df.columns
        has_atr = 'atr' in df.columns or 'risk_atr' in df.columns or 'atr_risk_mult' in df.columns
        print(f"Has ADX: {has_adx} | Has ATR: {has_atr}")
        print("Date min:", df['entry_time'].min() if 'entry_time' in df.columns else "N/A")
        print("Date max:", df['entry_time'].max() if 'entry_time' in df.columns else "N/A")
