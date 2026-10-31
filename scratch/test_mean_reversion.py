import pandas as pd
import numpy as np
import os
import glob
from scratch.evaluate_pruned_indicators_strategy import load_data

def test_mean_reversion_indicators(sym):
    df = load_data(sym, 'M15')
    if df is None: return None
    
    close = df['close'].values
    high = df['high'].values
    low = df['low'].values
    opens = df['open'].values
    times = df['time'].values
    
    # Bollinger Bands (20, 2.0)
    sma20 = pd.Series(close).rolling(20).mean().values
    std20 = pd.Series(close).rolling(20).std().values
    bb_upper = sma20 + 2.0 * std20
    bb_lower = sma20 - 2.0 * std20
    
    # RSI (7)
    delta = pd.Series(close).diff().values
    up = pd.Series(np.clip(delta, 0.0, None)).ewm(alpha=1.0/7, adjust=False).mean().values
    down = pd.Series(np.clip(-delta, 0.0, None)).ewm(alpha=1.0/7, adjust=False).mean().values
    rs = np.where(down == 0, 100.0, up / np.where(down == 0, 1e-9, down))
    rsi7 = 100.0 - (100.0 / (1.0 + rs))
    
    # ATR
    prev_close = np.roll(close, 1)
    prev_close[0] = close[0]
    tr = np.maximum(high - low, np.maximum(np.abs(high - prev_close), np.abs(low - prev_close)))
    atr = pd.Series(tr).ewm(alpha=1.0/14, adjust=False).mean().values
    
    trades = []
    in_pos = False
    direction = 0
    entry = sl = tp1 = tp2 = 0.0
    tp1_hit = False
    spread_cost_r = 0.03
    
    for i in range(25, len(times) - 1):
        if in_pos:
            h, l = high[i], low[i]
            if direction == 1: # BUY
                if l <= sl:
                    trades.append((0.5 * 1.0 + 0.5 * 0.0 - spread_cost_r) if tp1_hit else (-1.0 - spread_cost_r))
                    in_pos = False
                    continue
                if h >= tp1 and not tp1_hit:
                    tp1_hit = True
                    sl = entry
                if h >= tp2:
                    trades.append(0.5 * 1.0 + 0.5 * 2.0 - spread_cost_r)
                    in_pos = False
                    continue
            else: # SELL
                if h >= sl:
                    trades.append((0.5 * 1.0 + 0.5 * 0.0 - spread_cost_r) if tp1_hit else (-1.0 - spread_cost_r))
                    in_pos = False
                    continue
                if l <= tp1 and not tp1_hit:
                    tp1_hit = True
                    sl = entry
                if l <= tp2:
                    trades.append(0.5 * 1.0 + 0.5 * 2.0 - spread_cost_r)
                    in_pos = False
                    continue
            continue
            
        a = atr[i]
        if np.isnan(a) or a <= 0: continue
        
        # Mean Reversion trigger:
        # Price closes outside or pierces lower band with RSI7 oversold < 25 -> BUY towards mean (SMA20)
        # Price closes outside or pierces upper band with RSI7 overbought > 75 -> SELL towards mean
        buy_cond = (low[i] <= bb_lower[i]) and (close[i] > opens[i]) and (rsi7[i] < 30.0)
        sell_cond = (high[i] >= bb_upper[i]) and (close[i] < opens[i]) and (rsi7[i] > 70.0)
        
        next_o = opens[i+1]
        if buy_cond:
            entry = next_o
            stop_dist = max(1.0 * a, (entry - low[i]) + 0.15 * a)
            sl = entry - stop_dist
            tp1 = entry + 1.0 * stop_dist
            tp2 = entry + 2.0 * stop_dist
            in_pos = True
            direction = 1
            tp1_hit = False
        elif sell_cond:
            entry = next_o
            stop_dist = max(1.0 * a, (high[i] - entry) + 0.15 * a)
            sl = entry + stop_dist
            tp1 = entry - 1.0 * stop_dist
            tp2 = entry - 2.0 * stop_dist
            in_pos = True
            direction = -1
            tp1_hit = False
            
    t_arr = np.array(trades)
    n = len(t_arr)
    if n == 0: return None
    return {
        'symbol': sym,
        'trades': n,
        'win_rate': round((t_arr > 0).mean() * 100, 1),
        'net_r': round(t_arr.sum(), 2),
        'r_per_trade': round(t_arr.mean(), 3),
        'h1_net_r': round(t_arr[:n//2].sum(), 2),
        'h2_net_r': round(t_arr[n//2:].sum(), 2),
        'both_positive': (t_arr[:n//2].sum() > 0 and t_arr[n//2:].sum() > 0)
    }

print("=== MEAN REVERSION (BOLLINGER + RSI-7) RESULTS ===")
for s in ['EURUSD', 'USDJPY', 'USDCHF', 'AUDUSD']:
    res = test_mean_reversion_indicators(s)
    if res:
        print(res)
