import sys, os
sys.path.insert(0, os.path.abspath('.'))
import pandas as pd
from marketdata.factory import build_market_data_provider
from strategy.malaysian_snr.malaysian_snr_strategy import MalaysianSNRStrategy
from strategy.malaysian_snr.config import MalaysianSNRConfig
from strategy.malaysian_snr.validation import av_levels, level_freshness

provider = build_market_data_provider('MT5')
symbols = ['Crash 500 Index', 'Step Index 500', 'Crash 600 Index', 'Step Index', 'Wall Street 30', 'BTCUSD', 'XAUUSD', 'Boom 1000 Index']

print("--- TESTING CANDLES AND CONTINUATION LEVELS ---")
for sym in symbols:
    h1 = provider.get_candles(sym, 'H1', count=80)
    m15 = provider.get_candles(sym, 'M15', count=60)
    if h1 is None or m15 is None or len(h1) < 28 or len(m15) < 20:
        continue
    levels = av_levels(h1)
    last_h1 = h1.iloc[-1]
    last_m15 = m15.iloc[-1]
    print(f"\n{sym}: {len(levels)} H1 levels found.")
    for lvl in levels[-3:]:
        fresh = level_freshness(h1, lvl, 1.0)
        print(f"  Level {lvl['type']} at {lvl['level']} | visits: {fresh['visits']} | body_inv: {fresh['body_invalidated']} | state: {fresh['state']}")
