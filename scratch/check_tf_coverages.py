import pandas as pd
from pathlib import Path

print(f"{'Archivo':40s} | {'Timeframe':9s} | {'Start':10s} | {'End':10s} | {'Días':5s} | {'Años':5s} | {'Filas':7s}")
print("-" * 95)

for p in sorted(Path("data").rglob("*.*")):
    if p.suffix in ['.csv', '.pkl'] and any(tf in p.name for tf in ['_M5', '_M15', '_H1']):
        try:
            if p.suffix == '.csv':
                df = pd.read_csv(p)
                col = 'time' if 'time' in df.columns else ('datetime' if 'datetime' in df.columns else df.columns[0])
                ts = pd.to_datetime(df[col], utc=True)
            else:
                df = pd.read_pickle(p)
                col = 'time' if 'time' in df.columns else None
                ts = pd.to_datetime(df[col] if col else df.index, utc=True)
            days = (ts.max() - ts.min()).days
            tf = 'M5' if '_M5' in p.name else ('M15' if '_M15' in p.name else 'H1')
            print(f"{p.name:40s} | {tf:9s} | {ts.min().strftime('%Y-%m-%d')} | {ts.max().strftime('%Y-%m-%d')} | {days:5d} | {days/365.25:4.1f} | {len(df):7d}")
        except Exception:
            continue
