import time
from datetime import datetime, timezone, timedelta
import MetaTrader5 as mt5
import pandas as pd

if not mt5.initialize():
    print("MT5 failed to initialize")
    exit(1)

now = datetime.now(timezone.utc)
start_12m = now - timedelta(days=365)
start_6m = now - timedelta(days=180)

test_symbols = [
    "Step Index",
    "Step Index 500",
    "Volatility 75 Index",
    "Volatility 25 Index",
    "Jump 50 Index",
    "Jump 10 Index",
]

print(f"Current UTC time: {now}")
for sym in test_symbols:
    t0 = time.time()
    mt5.symbol_select(sym, True)
    rates_m15 = mt5.copy_rates_range(sym, mt5.TIMEFRAME_M15, start_6m, now)
    rates_h1 = mt5.copy_rates_range(sym, mt5.TIMEFRAME_H1, start_12m, now)
    m15_len = len(rates_m15) if rates_m15 is not None else 0
    h1_len = len(rates_h1) if rates_h1 is not None else 0
    dt = time.time() - t0
    print(f"{sym}: M15 (6m) = {m15_len} bars, H1 (12m) = {h1_len} bars. Fetched in {dt:.2f}s")

mt5.shutdown()
