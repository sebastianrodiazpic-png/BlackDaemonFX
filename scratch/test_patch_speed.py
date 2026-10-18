import sys
import time
from pathlib import Path
import pandas as pd
import numpy as np

PROJECT_ROOT = Path('.').resolve()
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Test fast closed_candles that does NOT modify any file on disk
import strategy.malaysian_snr.validation as val_mod
import strategy.malaysian_snr.history as hist_mod

orig_closed_candles = val_mod.closed_candles

def fast_closed_candles(raw, timeframe, now):
    if raw is None or raw.empty:
        return pd.DataFrame(columns=["time", "open", "high", "low", "close"])
    delta = val_mod.timeframe_delta(timeframe)
    # raw['time'] is already datetime64[ns, UTC]
    mask = (raw['time'] + delta) <= now
    return raw[mask].copy()

from tools.replay_msnr_live_faithful import HistoricalProvider
from strategy.malaysian_snr.malaysian_snr_strategy import MalaysianSNRStrategy
from strategy.malaysian_snr.config import MalaysianSNRConfig

cache_dir = PROJECT_ROOT / 'data' / 'cache_msnr'
m15 = pd.read_pickle(cache_dir / 'Boom_300_Index_M15.pkl')
h1 = pd.read_pickle(cache_dir / 'Boom_300_Index_H1.pkl')
col_m15 = 'time' if 'time' in m15.columns else m15.columns[0]
m15['time'] = pd.to_datetime(m15[col_m15], utc=True)
col_h1 = 'time' if 'time' in h1.columns else h1.columns[0]
h1['time'] = pd.to_datetime(h1[col_h1], utc=True)

df = h1.copy().set_index('time')
d1 = df.resample('1D').agg({'open':'first','high':'max','low':'min','close':'last','tick_volume':'sum'}).dropna().reset_index()

frames = {'M15': m15, 'H1': h1, 'D1': d1}
provider = HistoricalProvider(frames)
cfg = MalaysianSNRConfig()
strat = MalaysianSNRStrategy(provider, cfg)

# Benchmark 50 calls with original
provider.now = m15['time'].iloc[-100]
t0 = time.time()
for _ in range(50):
    res_orig = strat.analyze_symbol('Boom 300 Index', now_utc=provider.now.to_pydatetime())
t_orig = time.time() - t0

# Monkey patch in memory only
hist_mod.closed_candles = fast_closed_candles
val_mod.closed_candles = fast_closed_candles

t0 = time.time()
for _ in range(50):
    res_fast = strat.analyze_symbol('Boom 300 Index', now_utc=provider.now.to_pydatetime())
t_fast = time.time() - t0

print(f"Original 50 calls: {t_orig:.4f}s ({t_orig/50*1000:.2f}ms/call)")
print(f"Fast 50 calls:     {t_fast:.4f}s ({t_fast/50*1000:.2f}ms/call)")
print(f"Speedup: {t_orig / t_fast:.2f}x")
print(f"Results identical: {res_orig == res_fast}")
