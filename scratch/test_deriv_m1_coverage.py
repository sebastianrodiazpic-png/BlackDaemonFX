import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import time
import pandas as pd
from marketdata.deriv import DerivMarketDataProvider

provider = DerivMarketDataProvider()
symbols = [
    "Boom 500 Index",
    "Crash 300 Index",
    "Boom 600 Index",
    "Jump 10 Index",
    "Crash 600 Index",
    "Boom 300 Index"
]

cutoff_str = "2026-10-15T17:35:16"
cutoff_dt = pd.to_datetime(cutoff_str, utc=True)

print(f"Target Cutoff: {cutoff_dt}")
for sym in symbols:
    try:
        t0 = time.time()
        # Request 1000 M1 candles (approx 16.6 hours of M1)
        df = provider.get_candles(sym, timeframe="M1", count=1000)
        dt = time.time() - t0
        if df is not None and not df.empty:
            min_t = df['time'].min()
            max_t = df['time'].max()
            covers_cutoff = min_t <= cutoff_dt
            gap_check = (df['time'].diff().dt.total_seconds() > 60).sum()
            print(f"[{sym}] Got {len(df)} candles in {dt:.2f}s | Min: {min_t} | Max: {max_t} | Covers Cutoff: {covers_cutoff} | Gaps > 1m: {gap_check}")
        else:
            print(f"[{sym}] Empty dataframe returned!")
    except Exception as e:
        print(f"[{sym}] Error: {e}")
