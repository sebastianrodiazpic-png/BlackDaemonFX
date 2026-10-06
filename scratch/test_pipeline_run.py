import sys
import time
from datetime import datetime, timezone
from pathlib import Path
import MetaTrader5 as mt5
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from strategy.execution.trade_pipeline import run_trade_pipeline, PipelineConfig
from backtesting.trade_simulator import simulate_all_trades, get_backtest_summary

if not mt5.initialize():
    print("Failed to initialize MT5")
    exit(1)

sym = "Volatility 75 Index"
rates = mt5.copy_rates_from_pos(sym, mt5.TIMEFRAME_M15, 0, 2000)
mt5.shutdown()

df = pd.DataFrame(rates)
df['time'] = pd.to_datetime(df['time'], unit='s', utc=True)
print(f"Running pipeline on {len(df)} candles of {sym}...")

t0 = time.time()
cfg = PipelineConfig(risk_reward_ratio=2.0)
res = run_trade_pipeline(df, config=cfg, symbol=sym)
dt = time.time() - t0

print(f"Completed in {dt:.2f}s!")
setups = res["setups"]
confirmations = res["confirmations"]
print(f"Setups: {len(setups)}, Confirmations: {len(confirmations)}")

if not confirmations.empty:
    print(confirmations[["entry_time", "direction", "entry_price", "stop_loss", "take_profit"]].head())
    sim = simulate_all_trades(candles=df, entries=confirmations)
    summary = get_backtest_summary(sim)
    print("Backtest Summary:", summary)
