import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from collections import Counter
import MetaTrader5 as mt5
import pandas as pd
from strategy.execution.trade_pipeline import run_trade_pipeline, PipelineConfig

if not mt5.initialize():
    print("MT5 failed")
    exit(1)

rates = mt5.copy_rates_from_pos("Volatility 75 Index", mt5.TIMEFRAME_M15, 0, 4000)
mt5.shutdown()

df = pd.DataFrame(rates)
df['time'] = pd.to_datetime(df['time'], unit='s', utc=True)
cfg = PipelineConfig(risk_reward_ratio=2.0)
res = run_trade_pipeline(df, config=cfg, symbol="Volatility 75 Index")

confirmations = res["confirmations"]
rejected = confirmations.attrs.get("rejected_candidates", [])
print(f"Setups: {len(res['setups'])}, Confirmations: {len(confirmations)}, Rejected: {len(rejected)}")

reasons = Counter()
for r in rejected:
    for reason in r.get("rejection_reasons", []):
        reasons[reason] += 1

print("\nTop Rejection Reasons:")
for reason, count in reasons.most_common(10):
    print(f"  {reason}: {count}")
