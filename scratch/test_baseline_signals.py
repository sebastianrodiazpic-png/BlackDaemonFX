import sys
sys.path.insert(0, ".")

import pandas as pd
import numpy as np
from datetime import datetime, timezone
from strategy.ict.ict_strategy import ICTSabriMalleStrategy, build_h4_candles_from_h1
from strategy.ict.config import ICTSabriMalleConfig

class H1HistoricalProvider:
    def __init__(self, df_h1, spread=0.00015):
        self.df_h1 = df_h1.copy()
        self.df_h1['time'] = pd.to_datetime(self.df_h1['time'], utc=True)
        self.df_h1 = self.df_h1.sort_values('time').reset_index(drop=True)
        self.spread = spread
        self.current_idx = 0

    def set_idx(self, idx):
        self.current_idx = idx

    def get_candles(self, symbol, timeframe, count=80):
        start = max(0, self.current_idx - count + 1)
        return self.df_h1.iloc[start : self.current_idx + 1].copy()

    def get_current_tick(self, symbol):
        c = float(self.df_h1['close'].iloc[self.current_idx])
        return {
            'time': self.df_h1['time'].iloc[self.current_idx],
            'ask': c + self.spread / 2.0,
            'bid': c - self.spread / 2.0,
            'spread': self.spread
        }

for sym, path, spread in [
    ('EURUSD', 'data/forex_historical/EURUSD_H1.csv', 0.00015),
    ('GBPUSD', 'data/forex_historical/GBPUSD_H1.csv', 0.00020),
    ('XAUUSD', 'data/historical/XAUUSD_H1.csv', 0.59)
]:
    df = pd.read_csv(path)
    df['time'] = pd.to_datetime(df['time'], utc=True)
    # Filter last 2 years: Oct 1, 2024 to Oct 1, 2026
    start_date = pd.Timestamp("2024-10-01 00:00:00", tz=timezone.utc)
    end_date = pd.Timestamp("2026-10-01 23:59:59", tz=timezone.utc)
    df = df[(df['time'] >= start_date - pd.Timedelta(days=15)) & (df['time'] <= end_date)].reset_index(drop=True)
    
    provider = H1HistoricalProvider(df, spread=spread)
    strat = ICTSabriMalleStrategy(provider, ICTSabriMalleConfig())
    
    signals = []
    # start from bar 60 (to have history)
    for i in range(60, len(df)):
        t_bar = df['time'].iloc[i]
        if t_bar < start_date:
            continue
        provider.set_idx(i)
        res = strat.analyze_symbol(sym, now_utc=t_bar)
        if res.get("valid"):
            sig = res["signal"]
            sig["bar_index"] = i
            signals.append(sig)
            
    print(f"{sym}: Generated {len(signals)} signals in baseline strategy between {start_date.date()} and {end_date.date()}")
    if signals:
        print(f"  Sample signal: {signals[0]}")
