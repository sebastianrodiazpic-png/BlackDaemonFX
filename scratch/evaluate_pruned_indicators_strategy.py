import pandas as pd
import numpy as np
import os
import glob

def load_data(symbol, tf):
    paths = [
        f"data/historical/{symbol}_{tf}.csv",
        f"data/forex_historical/{symbol}_{tf}.csv",
    ]
    for p in paths:
        if os.path.exists(p):
            df = pd.read_csv(p)
            df['time'] = pd.to_datetime(df['time'])
            df = df.sort_values('time').reset_index(drop=True)
            return df
    return None

def calc_indicators(df, ema_fast=21, ema_slow=50, adx_p=14, rsi_p=14):
    df = df.copy()
    close = df['close'].values
    high = df['high'].values
    low = df['low'].values
    
    # EMA fast and slow
    df['ema_fast'] = df['close'].ewm(span=ema_fast, adjust=False).mean()
    df['ema_slow'] = df['close'].ewm(span=ema_slow, adjust=False).mean()
    
    # ATR
    prev_close = np.roll(close, 1)
    prev_close[0] = close[0]
    tr = np.maximum(high - low, np.maximum(np.abs(high - prev_close), np.abs(low - prev_close)))
    df['atr'] = pd.Series(tr).ewm(alpha=1.0/14, adjust=False).mean().values
    
    # RSI
    delta = pd.Series(close).diff().values
    up = pd.Series(np.clip(delta, 0.0, None)).ewm(alpha=1.0/rsi_p, adjust=False).mean().values
    down = pd.Series(np.clip(-delta, 0.0, None)).ewm(alpha=1.0/rsi_p, adjust=False).mean().values
    rs = np.where(down == 0, 100.0, up / np.where(down == 0, 1e-9, down))
    df['rsi'] = 100.0 - (100.0 / (1.0 + rs))
    
    # ADX
    plus_dm = np.clip(pd.Series(high).diff().values, 0.0, None)
    minus_dm = np.clip(-pd.Series(low).diff().values, 0.0, None)
    mask = plus_dm <= minus_dm
    plus_dm[mask] = 0.0
    mask2 = minus_dm <= plus_dm
    minus_dm[mask2] = 0.0
    
    tr_s = pd.Series(tr).ewm(alpha=1.0/adx_p, adjust=False).mean().values
    tr_s = np.where(tr_s == 0, 1e-9, tr_s)
    plus_di = 100.0 * (pd.Series(plus_dm).ewm(alpha=1.0/adx_p, adjust=False).mean().values / tr_s)
    minus_di = 100.0 * (pd.Series(minus_dm).ewm(alpha=1.0/adx_p, adjust=False).mean().values / tr_s)
    denom = plus_di + minus_di
    denom = np.where(denom == 0, 1e-9, denom)
    dx = 100.0 * (np.abs(plus_di - minus_di) / denom)
    df['adx'] = pd.Series(dx).ewm(alpha=1.0/adx_p, adjust=False).mean().values
    df['plus_di'] = plus_di
    df['minus_di'] = minus_di
    return df

def fast_simulate(df_merged, symbol, spread_cost_r=0.03):
    times = df_merged['time'].values
    opens = df_merged['open'].values
    highs = df_merged['high'].values
    lows = df_merged['low'].values
    closes = df_merged['close'].values
    atrs = df_merged['atr'].values
    rsis = df_merged['rsi'].values
    ema_fasts = df_merged['ema_fast'].values
    
    htf_fasts = df_merged['htf_ema_fast'].values
    htf_slows = df_merged['htf_ema_slow'].values
    htf_adxs = df_merged['htf_adx'].values
    htf_plus = df_merged['htf_plus_di'].values
    htf_minus = df_merged['htf_minus_di'].values
    
    is_crash = 'Crash' in symbol
    
    in_pos = False
    direction = 0 # 1 BUY, -1 SELL
    entry = 0.0
    sl = 0.0
    tp1 = 0.0
    tp2 = 0.0
    tp1_hit = False
    
    trades = []
    n = len(times)
    
    for i in range(50, n - 1):
        # 1. Manage active trade
        if in_pos:
            h = highs[i]
            l = lows[i]
            if direction == 1: # BUY
                if l <= sl:
                    realized_r = (0.5 * 1.0 + 0.5 * 0.0 - spread_cost_r) if tp1_hit else (-1.0 - spread_cost_r)
                    trades.append(realized_r)
                    in_pos = False
                    continue
                if h >= tp1 and not tp1_hit:
                    tp1_hit = True
                    sl = entry # BE
                if h >= tp2:
                    realized_r = 0.5 * 1.0 + 0.5 * 2.0 - spread_cost_r
                    trades.append(realized_r)
                    in_pos = False
                    continue
            else: # SELL
                if h >= sl:
                    realized_r = (0.5 * 1.0 + 0.5 * 0.0 - spread_cost_r) if tp1_hit else (-1.0 - spread_cost_r)
                    trades.append(realized_r)
                    in_pos = False
                    continue
                if l <= tp1 and not tp1_hit:
                    tp1_hit = True
                    sl = entry
                if l <= tp2:
                    realized_r = 0.5 * 1.0 + 0.5 * 2.0 - spread_cost_r
                    trades.append(realized_r)
                    in_pos = False
                    continue
            continue
            
        # 2. Check entry condition
        # HTF trend
        h_fast = htf_fasts[i]
        h_slow = htf_slows[i]
        h_adx = htf_adxs[i]
        h_p = htf_plus[i]
        h_m = htf_minus[i]
        
        htf_bull = (h_fast > h_slow) and (h_p > h_m) and (h_adx >= 18.0)
        htf_bear = (h_fast < h_slow) and (h_m > h_p) and (h_adx >= 18.0)
        
        atr = atrs[i]
        if np.isnan(atr) or atr <= 0: continue
        
        c = closes[i]
        o = opens[i]
        l = lows[i]
        h = highs[i]
        ef = ema_fasts[i]
        rsi = rsis[i]
        
        # Pullback condition
        bull_pb = (l <= ef) and (c > o) and (c > ef) and (35.0 <= rsi <= 68.0)
        bear_pb = (h >= ef) and (c < o) and (c < ef) and (32.0 <= rsi <= 65.0)
        
        if is_crash:
            bull_pb = False # Crash 1000 SELL ONLY
            
        next_o = opens[i+1]
        
        if htf_bull and bull_pb:
            entry = next_o
            stop_dist = max(1.1 * atr, (entry - l) + 0.15 * atr)
            sl = entry - stop_dist
            tp1 = entry + 1.0 * stop_dist
            tp2 = entry + 2.0 * stop_dist
            in_pos = True
            direction = 1
            tp1_hit = False
        elif htf_bear and bear_pb:
            entry = next_o
            stop_dist = max(1.1 * atr, (h - entry) + 0.15 * atr)
            sl = entry + stop_dist
            tp1 = entry - 1.0 * stop_dist
            tp2 = entry - 2.0 * stop_dist
            in_pos = True
            direction = -1
            tp1_hit = False
            
    return np.array(trades)

pruned_symbols = [
    'EURUSD', 'USDJPY', 'USDCAD', 'AUDUSD', 'USDCHF',
    'US_SP_500', 'XAGUSD', 'US_Oil', 'Crash_1000_Index', 'BTCUSD'
]

results = []
for sym in pruned_symbols:
    df_h1 = load_data(sym, 'H1')
    df_ltf = load_data(sym, 'M15')
    tf_name = 'H1+M15'
    if df_ltf is None:
        df_ltf = load_data(sym, 'M5')
        tf_name = 'H1+M5'
    if df_h1 is None or df_ltf is None:
        continue
        
    df_h1 = calc_indicators(df_h1, ema_fast=21, ema_slow=50, adx_p=14, rsi_p=14)
    df_ltf = calc_indicators(df_ltf, ema_fast=13, ema_slow=34, adx_p=14, rsi_p=14)
    
    df_ltf['htf_time'] = df_ltf['time'].dt.floor('1h')
    htf_sig = df_h1[['time', 'ema_fast', 'ema_slow', 'adx', 'plus_di', 'minus_di']].copy()
    htf_sig.columns = ['htf_time', 'htf_ema_fast', 'htf_ema_slow', 'htf_adx', 'htf_plus_di', 'htf_minus_di']
    
    merged = pd.merge_asof(df_ltf.sort_values('time'), htf_sig.sort_values('htf_time'), on='htf_time', direction='backward')
    merged = merged.dropna(subset=['htf_ema_fast', 'ema_fast', 'atr']).reset_index(drop=True)
    
    trades = fast_simulate(merged, sym)
    n = len(trades)
    if n > 0:
        wr = (trades > 0).mean() * 100
        net_r = trades.sum()
        r_per_trade = trades.mean()
        # Half 1 vs Half 2 test
        mid = n // 2
        h1_r = trades[:mid].sum()
        h2_r = trades[mid:].sum()
        results.append({
            'symbol': sym,
            'timeframe': tf_name,
            'trades': n,
            'win_rate': round(wr, 1),
            'net_r': round(net_r, 2),
            'r_per_trade': round(r_per_trade, 3),
            'h1_net_r': round(h1_r, 2),
            'h2_net_r': round(h2_r, 2),
            'both_positive': (h1_r > 0 and h2_r > 0)
        })

rdf = pd.DataFrame(results)
print("\n=== SIMULATION RESULTS (FAST NUMPY) ===")
print(rdf.to_string(index=False))
print(f"\nTOTAL TRADES GENERATED: {rdf['trades'].sum()}")
print(f"TOTAL NET R: {rdf['net_r'].sum():.2f}")
print(f"AVERAGE WIN RATE: {rdf['win_rate'].mean():.1f}%")
