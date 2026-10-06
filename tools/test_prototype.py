import sys
import os
import pandas as pd
import numpy as np

# Load EURUSD H1 and M15
h1_path = "data/forex_historical/EURUSD_H1.csv"
m15_path = "data/forex_historical/EURUSD_M15.csv"

df_h1 = pd.read_csv(h1_path)
df_h1['time'] = pd.to_datetime(df_h1['time'], utc=True)
df_h1 = df_h1.sort_values('time').reset_index(drop=True)

df_m15 = pd.read_csv(m15_path)
df_m15['time'] = pd.to_datetime(df_m15['time'], utc=True)
df_m15 = df_m15.sort_values('time').reset_index(drop=True)

print(f"Loaded EURUSD: H1={len(df_h1)}, M15={len(df_m15)}")
print(f"Date range: {df_h1['time'].iloc[0]} to {df_h1['time'].iloc[-1]}")
