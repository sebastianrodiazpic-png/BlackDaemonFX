import MetaTrader5 as mt5
import pandas as pd
from datetime import datetime, timezone

if not mt5.initialize():
    print("MT5 initialization failed:", mt5.last_error())
    exit(1)

symbols = [
    "XAUUSD",
    "Wall Street 30",
    "US Tech 100",
    "BTCUSD",
    "US Oil",
    "US SP 500",
    "XAGUSD"
]

print("Checking symbol coverage...")
results = []
for sym in symbols:
    selected = mt5.symbol_select(sym, True)
    info = mt5.symbol_info(sym)
    spread = info.spread * info.point if info else 0.0
    
    # Try M5
    rates_m5 = mt5.copy_rates_from_pos(sym, mt5.TIMEFRAME_M5, 0, 95000)
    n_m5 = len(rates_m5) if rates_m5 is not None else 0
    t0_m5 = pd.to_datetime(rates_m5[0]['time'], unit='s', utc=True) if n_m5 > 0 else None
    t1_m5 = pd.to_datetime(rates_m5[-1]['time'], unit='s', utc=True) if n_m5 > 0 else None

    # Try H1
    rates_h1 = mt5.copy_rates_from_pos(sym, mt5.TIMEFRAME_H1, 0, 30000)
    n_h1 = len(rates_h1) if rates_h1 is not None else 0
    t0_h1 = pd.to_datetime(rates_h1[0]['time'], unit='s', utc=True) if n_h1 > 0 else None
    t1_h1 = pd.to_datetime(rates_h1[-1]['time'], unit='s', utc=True) if n_h1 > 0 else None

    results.append({
        "symbol": sym,
        "spread_points": info.spread if info else 0,
        "spread_price": spread,
        "m5_count": n_m5,
        "m5_start": str(t0_m5),
        "m5_end": str(t1_m5),
        "h1_count": n_h1,
        "h1_start": str(t0_h1),
        "h1_end": str(t1_h1),
    })
    print(f"[{sym}] M5: {n_m5} ({t0_m5} to {t1_m5}) | H1: {n_h1} ({t0_h1} to {t1_h1}) | Spread: {spread:.4f}")

df = pd.DataFrame(results)
print("\nSummary:")
print(df.to_string())
mt5.shutdown()
