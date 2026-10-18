import sys
import cProfile
import pstats
from pathlib import Path
import pandas as pd

PROJECT_ROOT = Path('.').resolve()
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import strategy.malaysian_snr.validation as val_mod
import strategy.malaysian_snr.history as hist_mod

def fast_closed_candles(raw, timeframe, now):
    if raw is None or raw.empty:
        return pd.DataFrame(columns=["time", "open", "high", "low", "close"])
    delta = val_mod.timeframe_delta(timeframe)
    mask = (raw['time'] + delta) <= now
    return raw[mask].copy()

hist_mod.closed_candles = fast_closed_candles
val_mod.closed_candles = fast_closed_candles

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

provider.now = m15['time'].iloc[-100]

pr = cProfile.Profile()
pr.enable()
for _ in range(50):
    strat.analyze_symbol('Boom 300 Index', now_utc=provider.now.to_pydatetime())
pr.disable()

ps = pstats.Stats(pr).sort_stats('cumulative')
ps.print_stats(20)
