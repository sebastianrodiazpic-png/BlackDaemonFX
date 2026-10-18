import sys, os
sys.path.insert(0, os.path.abspath('.'))
import pandas as pd
from marketdata.factory import build_market_data_provider
from strategy.malaysian_snr.malaysian_snr_strategy import MalaysianSNRStrategy
from strategy.malaysian_snr.config import MalaysianSNRConfig

provider = build_market_data_provider('MT5')
now = pd.Timestamp.now(tz='UTC')

symbols = ['Crash 500 Index', 'Step Index 500', 'Crash 600 Index', 'Step Index', 'Wall Street 30', 'BTCUSD', 'XAUUSD']

for sym in symbols:
    try:
        raw_h1 = provider.get_candles(sym, 'H1', count=80)
        raw_m15 = provider.get_candles(sym, 'M15', count=60)
        print(f"Symbol: {sym} | H1 rows: {len(raw_h1) if raw_h1 is not None else 0} | M15 rows: {len(raw_m15) if raw_m15 is not None else 0}")
    except Exception as e:
        print(f"Symbol: {sym} error: {e}")
