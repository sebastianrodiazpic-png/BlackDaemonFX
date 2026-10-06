import os
import time
import pandas as pd
import numpy as np
from datetime import datetime
from scratch.test_strategy_runner import HistoricalDataProvider
from strategy.gold_quarters import GoldQuarterStrategy
from strategy.orb.new_york_orb import NewYorkORBStrategy, ORBConfig

def scan_gold_quarters(m5_df, h1_df, spread=0.59):
    print("Starting Gold Quarters scan...", flush=True)
    m5_df = m5_df.copy()
    m5_df['time'] = pd.to_datetime(m5_df['time'], utc=True)
    h1_df = h1_df.copy()
    h1_df['time'] = pd.to_datetime(h1_df['time'], utc=True)
    
    # Gold Quarters uses:
    # rejection = m5.iloc[-2], confirmation = m5.iloc[-1]
    # tolerance check on rejection extreme: round(extreme / 25) * 25
    # wick >= 45% of span
    # We can pre-filter M5 bars that are near 25 increments to make scanning 100x faster!
    signals = []
    
    # Pre-filtering candidates:
    # A bar can only be rejection if its low is within 2.5 of a quarter (for BUY) or its high is within 2.5 of a quarter (for SELL)
    # And span > 0 and wick / span >= 0.40
    # Let's vectorize candidate detection!
    highs = m5_df['high'].values
    lows = m5_df['low'].values
    opens = m5_df['open'].values
    closes = m5_df['close'].values
    times = m5_df['time'].values
    n = len(m5_df)
    
    # Find candidate rejection bars
    candidate_indices = []
    for i in range(20, n - 1):
        # Check BUY rejection: low near quarter
        low = lows[i]
        q_low = round(low / 25.0) * 25.0
        dist_low = abs(low - q_low)
        span = highs[i] - lows[i]
        
        # Check SELL rejection: high near quarter
        high = highs[i]
        q_high = round(high / 25.0) * 25.0
        dist_high = abs(high - q_high)
        
        if (dist_low <= 5.0 or dist_high <= 5.0) and span > 0:
            candidate_indices.append(i + 1) # confirmation bar index

    print(f"Total M5 bars: {n}, pre-filtered candidates: {len(candidate_indices)}", flush=True)
    
    provider = HistoricalDataProvider(m5_df, h1_df, spread=spread)
    gq = GoldQuarterStrategy(provider, increment=25.0, tolerance=2.0, min_rr=1.5)
    
    for idx in candidate_indices:
        t_conf = pd.Timestamp(times[idx])
        row_conf = m5_df.iloc[idx]
        eval_time = t_conf + pd.Timedelta(minutes=5)
        provider.set_time(eval_time, row_conf)
        res = gq.analyze_symbol('XAUUSD', now_utc=eval_time)
        if res.get('valid'):
            sig = res['signal']
            sig['bar_index'] = idx
            sig['confirmation_time'] = t_conf
            signals.append(sig)

    print(f"Gold Quarters scan complete! Found {len(signals)} confirmed signals.", flush=True)
    return signals

if __name__ == '__main__':
    m5 = pd.read_csv('data/historical/XAUUSD_M5.csv')
    h1 = pd.read_csv('data/historical/XAUUSD_H1.csv')
    t0 = time.time()
    sigs = scan_gold_quarters(m5, h1)
    print(f"Elapsed time: {time.time() - t0:.2f}s")
    if sigs:
        df_sigs = pd.DataFrame(sigs)
        print(df_sigs[['direction', 'entry_time', 'entry_price', 'stop_loss', 'quarter_target', 'quarter_target_2']].head(10))
