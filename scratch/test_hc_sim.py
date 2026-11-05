import pandas as pd
from datetime import datetime, timezone
from strategy.human_criteria.human_criteria_engine import HumanCriteriaEngine
from strategy.human_criteria.config import HumanCriteriaConfig

engine = HumanCriteriaEngine(HumanCriteriaConfig(enabled=True, mode='FILTER', malaysian_snr_min_score_threshold=60.0))

now = datetime.now(timezone.utc)
times = [now - pd.Timedelta(hours=i) for i in range(50, -1, -1)]
closes = [100.0 + i*0.5 for i in range(51)]
df_h1 = pd.DataFrame({'time': times, 'open': closes, 'high': [c+1 for c in closes], 'low': [c-1 for c in closes], 'close': closes})

signal = {'strategy_name': 'MALAYSIAN_SNR', 'symbol': 'Volatility 50 (1s) Index', 'direction': 'BUY', 'timeframe': 'M15', 'entry_price': 125.0, 'sl': 124.0, 'tp': 127.0}
decision = engine.evaluate_candidate(symbol='Volatility 50 (1s) Index', direction='BUY', signal=signal, df_h1=df_h1, df_ltf=df_h1)

print('Decision allowed:', decision.allowed)
print('Decision action:', decision.action)
print('Decision reason:', decision.reason)
print('Total score:', decision.score)
print('Breakdown:', decision.breakdown.to_dict())
