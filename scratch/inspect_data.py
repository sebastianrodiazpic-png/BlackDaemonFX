import pandas as pd

for s in ['XAUUSD_M5.csv', 'BTCUSD_M5.csv', 'USDCAD_M5.csv', 'AUDUSD_M5.csv', 'US_Oil_M5.csv']:
    path = f'storage/analysis/orb_sweep_expanded/history/{s}'
    df = pd.read_csv(path)
    print(f"{s}: {len(df)} rows, cols: {list(df.columns)}, from {df['time'].iloc[0]} to {df['time'].iloc[-1]}")
