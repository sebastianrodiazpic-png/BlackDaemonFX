"""Controlled examples of retest expiry, CRT tolerance and disabled fresh gate."""
import json
import sys
from dataclasses import replace
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import pandas as pd
from strategy.malaysian_snr.config import MalaysianSNRConfig
from strategy.malaysian_snr.malaysian_snr_strategy import MalaysianSNRStrategy
from strategy.malaysian_snr.validation import confirmed_retest, confirmed_crt_retest

def candles(freq='h', count=40, start='2026-10-08'):
    return pd.DataFrame({'time': pd.date_range(start, periods=count, freq=freq, tz='UTC'),
                         'open': 100., 'high': 102., 'low': 98., 'close': 101.})

class Provider:
    def __init__(self, frames):
        self.frames = frames
    def get_candles(self, symbol, timeframe, count=100):
        return self.frames.get(timeframe, pd.DataFrame()).tail(count)

h1 = candles()
h1.loc[37, ['open','high','low','close']] = [100,103,99,101]
h1.loc[38, ['open','high','low','close']] = [100,102,97,100.5]
h1.loc[39, ['open','high','low','close']] = [99,105,98,104]
break_close = h1.time.iloc[-1] + pd.Timedelta(hours=1)
m15 = candles('15min',60,break_close-pd.Timedelta(hours=14,minutes=45))
m15.loc[59,['open','high','low','close']] = [102.9,103.8,102.8,103.3]
config = MalaysianSNRConfig(allowed_symbols=(), enable_daily_storyline_filter=False)
provider = Provider({'H1':h1,'M15':m15})
strategy = MalaysianSNRStrategy(provider, config)
first = strategy.analyze_symbol('Step Index', break_close+pd.Timedelta(minutes=15))
assert first['valid']
provider.frames['H1'] = pd.concat([h1, pd.DataFrame([{'time':break_close,'open':104.8,
    'high':105.5,'low':104.4,'close':104.8}])], ignore_index=True)
later = candles('15min',4,break_close+pd.Timedelta(minutes=15))
later[['open','high','low','close']] = [104.6,105.2,104.4,104.8]
later.loc[3,['open','high','low','close']] = [102.9,103.8,102.8,103.3]
# Alternate path: the first actual visit occurs after the next H1 closes.
late_m15 = m15.copy()
late_m15.loc[59,['open','high','low','close']] = [104.8,105.2,104.6,105.]
provider.frames['M15'] = pd.concat([late_m15,later],ignore_index=True)
late = strategy.analyze_symbol('Step Index',break_close+pd.Timedelta(minutes=75))
assert not late['valid'] and late['reason'] == 'NO_SETUP_CONFIRMED'
assert confirmed_crt_retest(later.tail(1),103,'BUY',2)
no_fresh = MalaysianSNRStrategy(provider,replace(config,enable_strict_fresh_filter=False))
assert late == no_fresh.analyze_symbol('Step Index',break_close+pd.Timedelta(minutes=75))

near = pd.DataFrame([{'open':100.5,'high':101.,'low':100.5,'close':100.8}])
below = pd.DataFrame([{'open':95.,'high':96.,'low':94.,'close':95.5},
                      {'open':100.5,'high':101.,'low':100.4,'close':100.8}])
probes = {
    'existing_fractal_at_15min': {'valid':first['valid'],'scenario':first['signal']['scenario']},
    'same_reference_at_75min': {'valid':late['valid'],'reason':late['reason'],
                              'late_m15_still_confirms_reference':True},
    'strict_fresh_off_same_result':True,
    'near_touch_buy_level100_atr2_low100_5': {
        'bounded_retest_0_35atr':confirmed_retest(near,100,'BUY',2,.35,.5),
        'crt_0_35atr_argument':confirmed_crt_retest(near,100,'BUY',2,.35,.5),
        'crt_0_90atr_argument':confirmed_crt_retest(near,100,'BUY',2,.90,.5)},
    'crt_can_link_below_zone_bar_to_later_recovery_without_zone_intersection':
        confirmed_crt_retest(below,100,'BUY',2),
    'note':'Controlled code behavior; these examples do not measure market profitability.',
}
assert probes['near_touch_buy_level100_atr2_low100_5']['bounded_retest_0_35atr']
assert not probes['near_touch_buy_level100_atr2_low100_5']['crt_0_90atr_argument']
assert probes['crt_can_link_below_zone_bar_to_later_recovery_without_zone_intersection']
out = ROOT/'storage/analysis/msnr_restriction_review_20261011'
out.mkdir(parents=True,exist_ok=True)
(out/'controlled_probes.json').write_text(json.dumps(probes,indent=2),encoding='utf-8')
print(json.dumps(probes,indent=2))
