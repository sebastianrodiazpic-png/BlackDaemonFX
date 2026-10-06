import os
import sys
import math
import numpy as np
import pandas as pd
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

NEW_YORK = ZoneInfo("America/New_York")

class FastHistoricalDataProvider:
    def __init__(self, m5_df, h1_df=None, spread=0.59):
        self.m5_df = m5_df.copy()
        if not pd.api.types.is_datetime64_any_dtype(self.m5_df['time']):
            self.m5_df['time'] = pd.to_datetime(self.m5_df['time'], utc=True)
        elif self.m5_df['time'].dt.tz is None:
            self.m5_df['time'] = self.m5_df['time'].dt.tz_localize('UTC')
        else:
            self.m5_df['time'] = self.m5_df['time'].dt.tz_convert('UTC')
            
        self.m5_df = self.m5_df.sort_values('time').reset_index(drop=True)
        self.m5_times = self.m5_df['time'].values

        if h1_df is not None:
            self.h1_df = h1_df.copy()
            if not pd.api.types.is_datetime64_any_dtype(self.h1_df['time']):
                self.h1_df['time'] = pd.to_datetime(self.h1_df['time'], utc=True)
            elif self.h1_df['time'].dt.tz is None:
                self.h1_df['time'] = self.h1_df['time'].dt.tz_localize('UTC')
            else:
                self.h1_df['time'] = self.h1_df['time'].dt.tz_convert('UTC')
            self.h1_df = self.h1_df.sort_values('time').reset_index(drop=True)
            self.h1_times = self.h1_df['time'].values
        else:
            self.h1_df = None
            self.h1_times = None

        self.spread = spread
        self.current_idx = len(self.m5_df) - 1
        self.current_time = self.m5_df['time'].iloc[-1]

    def set_index(self, idx):
        self.current_idx = idx
        self.current_time = self.m5_df['time'].iloc[idx]

    def get_candles(self, symbol, timeframe, count=350):
        tf = str(timeframe).upper()
        if tf == 'M5':
            start_i = max(0, self.current_idx - count + 1)
            return self.m5_df.iloc[start_i : self.current_idx + 1].copy()
        elif tf == 'H1' and self.h1_df is not None:
            # find index in H1 up to current_time
            t_val = self.m5_times[self.current_idx]
            h1_idx = np.searchsorted(self.h1_times, t_val, side='right')
            start_i = max(0, h1_idx - count)
            return self.h1_df.iloc[start_i : h1_idx].copy()
        else:
            start_i = max(0, self.current_idx - count + 1)
            return self.m5_df.iloc[start_i : self.current_idx + 1].copy()

    def get_current_tick(self, symbol):
        close = float(self.m5_df['close'].iloc[self.current_idx])
        return {
            'time': self.current_time.to_pydatetime(),
            'ask': close + self.spread / 2.0,
            'bid': close - self.spread / 2.0,
            'last': close,
            'spread': self.spread
        }

print("FastHistoricalDataProvider ready")
