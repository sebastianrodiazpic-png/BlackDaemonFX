import pandas as pd
from pathlib import Path

ROOT = Path("c:/TradingBoot/smc_synthetic_bot")

files_to_check = [
    ROOT / "data/historical/XAUUSD_M15.csv",
    ROOT / "data/historical/BTCUSD_M15.csv",
    ROOT / "data/historical/Wall_Street_30_M15.csv",
    ROOT / "data/historical/Step_Index_M5.csv",
    ROOT / "data/historical/Boom_1000_Index_M5.csv",
    ROOT / "data/forex_historical/EURUSD_M5.csv",
    ROOT / "storage/analysis/orb_nunez_2y/history/XAUUSD_M5.csv",
    ROOT / "storage/analysis/orb_nunez_2y/history/Wall_Street_30_M5.csv",
]

print("=== CHECKING DATE RANGES IN EXISTING DATASETS ===")
for f in files_to_check:
    if f.exists():
        try:
            df = pd.read_csv(f)
            time_col = [c for c in df.columns if c.lower() in ['time', 'date', 'datetime', 'timestamp']][0]
            start_date = df[time_col].iloc[0]
            end_date = df[time_col].iloc[-1]
            total_bars = len(df)
            print(f"{f.name:25s} | Bars: {total_bars:7d} | Start: {start_date} | End: {end_date}")
        except Exception as e:
            print(f"{f.name:25s} | Error: {e}")
    else:
        print(f"{f.name:25s} | Not found")
