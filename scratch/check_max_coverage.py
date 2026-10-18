import pandas as pd
from pathlib import Path

print("--- Checking maximum date span across all files in data/ ---")
max_days = 0
best_file = None

for p in Path("data").rglob("*.*"):
    if p.suffix in ['.csv', '.pkl']:
        try:
            if p.suffix == '.csv':
                df = pd.read_csv(p, nrows=500000)
                col = 'time' if 'time' in df.columns else ('datetime' if 'datetime' in df.columns else None)
                if col is None:
                    continue
                ts = pd.to_datetime(df[col], utc=True)
            else:
                df = pd.read_pickle(p)
                col = 'time' if 'time' in df.columns else None
                ts = pd.to_datetime(df[col] if col else df.index, utc=True)
            days = (ts.max() - ts.min()).days
            if days > max_days:
                max_days = days
                best_file = p
        except Exception:
            continue

print(f"Max coverage found: {max_days} days (~{max_days/365.25:.2f} years) in file: {best_file}")
