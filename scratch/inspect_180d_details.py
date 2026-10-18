import pandas as pd
from pathlib import Path

df1 = pd.read_csv('storage/analysis/replay_boom_crash_forex_gold_180d_trades.csv')
print('=== df1 (boom crash forex gold 180d) ===')
print('Dates:', df1['entry_time'].min(), 'to', df1['entry_time'].max())
print('Symbol counts:\n', df1['symbol'].value_counts())

df2 = pd.read_csv('storage/analysis/replay_step_vol_jump_180d_trades.csv')
print('\n=== df2 (step vol jump 180d) ===')
print('Dates:', df2['entry_time'].min(), 'to', df2['entry_time'].max())
print('Symbol counts:\n', df2['symbol'].value_counts())
