import sys
sys.path.insert(0, '.')
import pandas as pd
from datetime import datetime, timezone

TIMEFRAME_MINUTES = {"M1": 1, "M5": 5, "M15": 15, "M30": 30, "H1": 60, "H4": 240, "D1": 1440}

def fixed_closed_candles_only(df: pd.DataFrame, timeframe: str, now: pd.Timestamp, count: int | None = None) -> pd.DataFrame:
    duration = pd.Timedelta(minutes=TIMEFRAME_MINUTES.get(str(timeframe).upper(), 0))
    t_col = df["time"]
    if isinstance(t_col.dtype, pd.DatetimeTZDtype) and str(t_col.dtype.tz) == "UTC" and t_col.is_monotonic_increasing:
        cutoff = now - duration
        try:
            unit_str = getattr(t_col.dt, "unit", None)
            if unit_str:
                cutoff_aligned = pd.Timestamp(cutoff).as_unit(unit_str, round_ok=True)
            else:
                cutoff_aligned = cutoff
            idx = int(t_col.searchsorted(cutoff_aligned, side="right"))
            start = max(0, idx - int(count)) if count is not None else 0
            return df.iloc[start:idx].reset_index(drop=True)
        except Exception:
            pass
    out = df.copy()
    out["time"] = pd.to_datetime(out["time"], utc=True)
    out = out[out["time"] + duration <= now].sort_values("time")
    if count is not None:
        out = out.tail(int(count))
    return out.reset_index(drop=True)

now = pd.Timestamp(datetime.now(timezone.utc))
for unit in ['s', 'ms', 'us', 'ns']:
    times = pd.date_range('2026-10-26', periods=50, freq='1h', unit=unit, tz='UTC')
    df = pd.DataFrame({
        'time': times,
        'open': [100.0]*50,
        'high': [105.0]*50,
        'low': [95.0]*50,
        'close': [102.0]*50,
    })
    res = fixed_closed_candles_only(df, 'H1', now, count=30)
    print(f"Unit {unit} with fix: SUCCESS! returned {len(res)} candles")
