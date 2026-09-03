from __future__ import annotations
from pathlib import Path
import pandas as pd


def update_historical_csv(provider, symbol: str, timeframe: str, count: int = 5000, output_dir: str | Path = "data/historical"):
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    safe_symbol = "_".join(symbol.replace("(", "").replace(")", "").split())
    path = output_dir / f"{safe_symbol}_{timeframe}.csv"

    fresh = provider.get_candles(symbol, timeframe=timeframe, count=count)
    if path.exists():
        old = pd.read_csv(path)
        old["time"] = pd.to_datetime(old["time"], utc=True)
        data = pd.concat([old, fresh], ignore_index=True)
    else:
        data = fresh.copy()
    data["time"] = pd.to_datetime(data["time"], utc=True)
    data = data.drop_duplicates(subset=["time"]).sort_values("time").reset_index(drop=True)
    data.to_csv(path, index=False)
    return path, len(data)
