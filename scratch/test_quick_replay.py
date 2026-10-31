import sys
from pathlib import Path
import time
import pandas as pd
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import tools.replay_orb_nunez_2y as R
from strategy.orb import new_york_orb as orb
from strategy.orb.asset_rules import ASSET_CONFIG, audit_volume_confirmation, check_range_amplitude

print("Testing replay on BTCUSD and XAUUSD...")
t0 = time.time()
df_btc, cov_btc = R.load("BTCUSD")
print(f"BTC loaded: {len(df_btc)} rows in {time.time()-t0:.2f}s")
