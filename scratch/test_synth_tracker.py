import sys, os
sys.path.insert(0, os.path.abspath('.'))
import pandas as pd
from scratch.test_session_tracker import track_session_liquidity

# Test Synthetics
t0 = pd.Timestamp('2026-10-13 00:00:00Z')
bars = []
for i in range(24):
    # Prior bars between 1000 and 1050
    bars.append({'time': t0 + pd.Timedelta(minutes=15*i), 'open': 1020, 'high': 1050, 'low': 1000, 'close': 1030})
# Current bar sweeps prior high to 1060 and rejects
bars.append({'time': t0 + pd.Timedelta(minutes=15*24), 'open': 1030, 'high': 1060, 'low': 1025, 'close': 1035})
df_synth = pd.DataFrame(bars)

res_synth_sell = track_session_liquidity(df_synth, 'Crash 500 Index', t0 + pd.Timedelta(minutes=15*25), direction='SELL')
print("Crash 500 Sell:", res_synth_sell)
assert res_synth_sell['sweep_confirmed'] is True
assert res_synth_sell['sweep_type'] == 'PRIOR_H4_HIGH_SWEPT'
assert res_synth_sell['swept_level'] == 1050.0

res_synth_buy = track_session_liquidity(df_synth, 'Crash 500 Index', t0 + pd.Timedelta(minutes=15*25), direction='BUY')
print("Crash 500 Buy:", res_synth_buy)
assert res_synth_buy['sweep_confirmed'] is False

print("SYNTHETICS TEST PASSED!")
