import pandas as pd
import numpy as np
from strategy.malaysian_snr.validation import av_levels

# Generar una serie simulada de 500 velas con oscilaciones típicas
np.random.seed(42)
n = 500
base = 1000.0 + np.cumsum(np.random.normal(0, 5, n))
highs = base + np.abs(np.random.normal(2, 2, n))
lows = base - np.abs(np.random.normal(2, 2, n))
opens = base + np.random.normal(0, 1, n)
closes = base + np.random.normal(0, 1, n)

df = pd.DataFrame({
    'time': pd.date_range('2026-01-01', periods=n, freq='1h'),
    'open': opens,
    'high': highs,
    'low': lows,
    'close': closes
})

engulfing_levels = av_levels(df, include_latest=False, definition='engulfing')
body_turns_levels = av_levels(df, include_latest=False, definition='body_turns')

print(f"Niveles con 'engulfing':  {len(engulfing_levels)}")
print(f"Niveles con 'body_turns': {len(body_turns_levels)}")
print(f"Incremento de niveles detectados: {((len(body_turns_levels)/len(engulfing_levels)) - 1)*100:.1f}%")
