import sys
import time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pandas as pd
import MetaTrader5 as mt5

from strategy.execution.trade_pipeline import run_trade_pipeline, PipelineConfig

if not mt5.initialize():
    exit(1)

rates = mt5.copy_rates_from_pos("Step Index", mt5.TIMEFRAME_M15, 0, 10000)
mt5.shutdown()

df = pd.DataFrame(rates)
df['time'] = pd.to_datetime(df['time'], unit='s', utc=True)

cfg_fast = PipelineConfig(
    risk_reward_ratio=2.0,
    chart_patterns_enabled=False,
    harmonic_enabled=False,
    divergence_enabled=False,
    fvg_enabled=True,
    fvg_min_displacement_atr_multiplier=1.5,
)

t0 = time.time()
res_fast = run_trade_pipeline(df, config=cfg_fast, symbol="Step Index")
dt_fast = time.time() - t0
print(f"Fast pipeline on 10,000 candles: {dt_fast:.2f}s | Setups: {len(res_fast['setups'])}, Confirmations: {len(res_fast['confirmations'])}")
