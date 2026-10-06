import sys
import time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pandas as pd
import MetaTrader5 as mt5

from strategy.smc.swings import detect_swings
from strategy.smc.market_structure import classify_market_structure
from strategy.smc.liquidity import detect_liquidity_levels
from strategy.smc.liquidity_sweeps import detect_liquidity_sweeps
from strategy.smc.choch_bos import detect_choch_bos
from strategy.smc.order_blocks import detect_order_blocks
from strategy.smc.premium_discount import calculate_premium_discount
from strategy.execution.trade_pipeline import PipelineConfig, build_setups
from strategy.smc.entry_confirmation import detect_entry_confirmations

if not mt5.initialize():
    exit(1)

rates = mt5.copy_rates_from_pos("Step Index", mt5.TIMEFRAME_M15, 0, 3000)
mt5.shutdown()

df = pd.DataFrame(rates)
df['time'] = pd.to_datetime(df['time'], unit='s', utc=True)
config = PipelineConfig(risk_reward_ratio=2.0)

steps = [
    ("detect_swings", lambda d: detect_swings(d, left=config.swing_left, right=config.swing_right)),
    ("classify_market_structure", classify_market_structure),
    ("detect_liquidity_levels", lambda d: detect_liquidity_levels(d, tolerance=config.liquidity_tolerance)),
    ("detect_liquidity_sweeps", detect_liquidity_sweeps),
    ("detect_choch_bos", detect_choch_bos),
    ("detect_order_blocks", lambda d: detect_order_blocks(d, lookback=config.order_block_lookback)),
    ("calculate_premium_discount", lambda d: calculate_premium_discount(d, lookback=config.premium_discount_lookback)),
]

data = df.copy()
for name, fn in steps:
    t0 = time.time()
    data = fn(data)
    print(f"{name}: {time.time() - t0:.3f}s")

t0 = time.time()
setups = build_setups(data, config)
print(f"build_setups: {time.time() - t0:.3f}s (found {len(setups)})")

t0 = time.time()
confs = detect_entry_confirmations(data, setups, max_wait_candles=config.max_retest_candles, min_wait_candles=config.min_retest_wait_candles)
print(f"detect_entry_confirmations: {time.time() - t0:.3f}s (found {len(confs)})")
