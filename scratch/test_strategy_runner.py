import os
import pandas as pd
from datetime import datetime, timezone
from strategy.gold_quarters import GoldQuarterStrategy
from strategy.orb.new_york_orb import NewYorkORBStrategy, ORBConfig

class HistoricalDataProvider:
    def __init__(self, m5_df, h1_df=None, spread=0.59):
        self.m5_df = m5_df.copy()
        self.m5_df['time'] = pd.to_datetime(self.m5_df['time'], utc=True)
        self.m5_df = self.m5_df.sort_values('time').reset_index(drop=True)
        
        if h1_df is not None:
            self.h1_df = h1_df.copy()
            self.h1_df['time'] = pd.to_datetime(self.h1_df['time'], utc=True)
            self.h1_df = self.h1_df.sort_values('time').reset_index(drop=True)
        else:
            self.h1_df = None
            
        self.spread = spread
        self.current_time = None
        self.current_bar = None

    def set_time(self, current_time, current_bar):
        self.current_time = current_time
        self.current_bar = current_bar

    def get_candles(self, symbol, timeframe, count=350):
        tf = str(timeframe).upper()
        if tf == 'M5':
            df = self.m5_df[self.m5_df['time'] <= self.current_time]
            return df.tail(count).copy()
        elif tf == 'H1' and self.h1_df is not None:
            df = self.h1_df[self.h1_df['time'] <= self.current_time]
            return df.tail(count).copy()
        else:
            df = self.m5_df[self.m5_df['time'] <= self.current_time]
            return df.tail(count).copy()

    def get_current_tick(self, symbol):
        close = float(self.current_bar['close'])
        return {
            'time': self.current_time.to_pydatetime(),
            'ask': close + self.spread / 2.0,
            'bid': close - self.spread / 2.0,
            'last': close,
            'spread': self.spread
        }

print("HistoricalDataProvider ready")
