import pandas as pd
from pathlib import Path

print("--- Inspecting date ranges in data/historical/ and data/cache_msnr/ ---")

csv_files = [
    "data/historical/Boom_1000_Index_M5.csv",
    "data/historical/Crash_1000_Index_M5.csv",
    "data/historical/Step_Index_M5.csv",
    "data/historical/XAUUSD_M5.csv",
    "data/historical/Wall_Street_30_M5.csv",
    "data/forex_historical/EURUSD_M5.csv",
    "data/forex_historical/USDJPY_M5.csv",
]

for f in csv_files:
    p = Path(f)
    if p.exists():
        df = pd.read_csv(p)
        time_col = 'time' if 'time' in df.columns else ('datetime' if 'datetime' in df.columns else df.columns[0])
        ts = pd.to_datetime(df[time_col], utc=True)
        days = (ts.max() - ts.min()).days
        print(f"{p.name:30s} | Start: {ts.min().strftime('%Y-%m-%d')} | End: {ts.max().strftime('%Y-%m-%d')} | Days: {days:4d} (~{days/365.25:.1f} yrs) | Rows: {len(df):6d}")

print("\n--- Inspecting sample PKL from cache_msnr/ ---")
pkl_files = [
    "data/cache_msnr/Boom_1000_Index_M15.pkl",
    "data/cache_msnr/Step_Index_M15.pkl",
    "data/cache_msnr/XAUUSD_M15.pkl",
    "data/cache_msnr/EURUSD_M15.pkl"
]
for f in pkl_files:
    p = Path(f)
    if p.exists():
        df = pd.read_pickle(p)
        time_col = 'time' if 'time' in df.columns else df.index
        ts = pd.to_datetime(df['time'] if 'time' in df.columns else df.index, utc=True)
        days = (ts.max() - ts.min()).days
        print(f"{p.name:30s} | Start: {ts.min().strftime('%Y-%m-%d')} | End: {ts.max().strftime('%Y-%m-%d')} | Days: {days:4d} (~{days/365.25:.1f} yrs) | Rows: {len(df):6d}")
