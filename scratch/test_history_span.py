import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import MetaTrader5 as mt5
import pandas as pd
from tools.replay_orb_1to2 import fetch_symbol_candles_chunked

if mt5.initialize():
    symbols = ['Wall Street 30', 'US Tech 100', 'US SP 500', 'XAUUSD', 'XAGUSD', 'US Oil', 'EURUSD', 'BTCUSD']
    for s in symbols:
        df = fetch_symbol_candles_chunked(s, mt5.TIMEFRAME_M5, days=1000)
        if df is not None and not df.empty:
            t_min = df['time'].min()
            t_max = df['time'].max()
            days_span = (t_max - t_min).days
            print(f"{s:15s}: {len(df):6d} candles | {t_min.strftime('%Y-%m-%d')} to {t_max.strftime('%Y-%m-%d')} ({days_span} days / {days_span/365.25:.2f} years)")
        else:
            print(f"{s:15s}: No data")
    mt5.shutdown()
else:
    print("MT5 Init Failed")
