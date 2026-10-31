import pandas as pd
import numpy as np
from scratch.evaluate_pruned_indicators_strategy import load_data, calc_indicators, fast_simulate

forex_pairs = ['EURUSD', 'USDJPY', 'USDCHF', 'AUDUSD']

print("=== TESTING SENSITIVITY ON PRUNED FOREX ===")
for adx_th in [20.0, 24.0, 28.0]:
    for rsi_low, rsi_high in [(40.0, 60.0), (35.0, 65.0)]:
        tot_trades = 0
        tot_r = 0.0
        for sym in forex_pairs:
            df_h1 = load_data(sym, 'H1')
            df_ltf = load_data(sym, 'M15')
            if df_h1 is None or df_ltf is None: continue
            
            df_h1 = calc_indicators(df_h1, ema_fast=34, ema_slow=89, adx_p=14)
            df_ltf = calc_indicators(df_ltf, ema_fast=13, ema_slow=34, adx_p=14)
            
            df_ltf['htf_time'] = df_ltf['time'].dt.floor('1h')
            htf_sig = df_h1[['time', 'ema_fast', 'ema_slow', 'adx', 'plus_di', 'minus_di']].copy()
            htf_sig.columns = ['htf_time', 'htf_ema_fast', 'htf_ema_slow', 'htf_adx', 'htf_plus_di', 'htf_minus_di']
            
            merged = pd.merge_asof(df_ltf.sort_values('time'), htf_sig.sort_values('htf_time'), on='htf_time', direction='backward')
            merged = merged.dropna(subset=['htf_ema_fast', 'ema_fast', 'atr']).reset_index(drop=True)
            
            # custom fast_simulate with adx_th
            times = merged['time'].values
            opens = merged['open'].values
            highs = merged['high'].values
            lows = merged['low'].values
            closes = merged['close'].values
            atrs = merged['atr'].values
            rsis = merged['rsi'].values
            ema_fasts = merged['ema_fast'].values
            htf_fasts = merged['htf_ema_fast'].values
            htf_slows = merged['htf_ema_slow'].values
            htf_adxs = merged['htf_adx'].values
            htf_plus = merged['htf_plus_di'].values
            htf_minus = merged['htf_minus_di'].values
            
            in_pos = False
            direction = 0
            entry = sl = tp1 = tp2 = 0.0
            tp1_hit = False
            trades = []
            
            for i in range(50, len(times)-1):
                if in_pos:
                    h, l = highs[i], lows[i]
                    if direction == 1:
                        if l <= sl:
                            trades.append((0.5 * 1.0 + 0.5 * 0.0 - 0.03) if tp1_hit else (-1.0 - 0.03))
                            in_pos = False
                            continue
                        if h >= tp1 and not tp1_hit:
                            tp1_hit = True
                            sl = entry
                        if h >= tp2:
                            trades.append(0.5 * 1.0 + 0.5 * 2.0 - 0.03)
                            in_pos = False
                            continue
                    else:
                        if h >= sl:
                            trades.append((0.5 * 1.0 + 0.5 * 0.0 - 0.03) if tp1_hit else (-1.0 - 0.03))
                            in_pos = False
                            continue
                        if l <= tp1 and not tp1_hit:
                            tp1_hit = True
                            sl = entry
                        if l <= tp2:
                            trades.append(0.5 * 1.0 + 0.5 * 2.0 - 0.03)
                            in_pos = False
                            continue
                    continue
                
                # HTF with higher ADX
                if htf_adxs[i] < adx_th: continue
                htf_bull = (htf_fasts[i] > htf_slows[i]) and (htf_plus[i] > htf_minus[i])
                htf_bear = (htf_fasts[i] < htf_slows[i]) and (htf_minus[i] > htf_plus[i])
                
                atr = atrs[i]
                if np.isnan(atr) or atr <= 0: continue
                c, o, l, h, ef, rsi = closes[i], opens[i], lows[i], highs[i], ema_fasts[i], rsis[i]
                
                bull_pb = (l <= ef) and (c > o) and (c > ef) and (rsi_low <= rsi <= rsi_high)
                bear_pb = (h >= ef) and (c < o) and (c < ef) and (rsi_low <= rsi <= rsi_high)
                
                next_o = opens[i+1]
                if htf_bull and bull_pb:
                    entry = next_o
                    dist = max(1.2 * atr, (entry - l) + 0.2 * atr)
                    sl = entry - dist
                    tp1 = entry + 1.0 * dist
                    tp2 = entry + 2.0 * dist
                    in_pos = True
                    direction = 1
                    tp1_hit = False
                elif htf_bear and bear_pb:
                    entry = next_o
                    dist = max(1.2 * atr, (h - entry) + 0.2 * atr)
                    sl = entry + dist
                    tp1 = entry - 1.0 * dist
                    tp2 = entry - 2.0 * dist
                    in_pos = True
                    direction = -1
                    tp1_hit = False
                    
            t_arr = np.array(trades)
            tot_trades += len(t_arr)
            tot_r += t_arr.sum()
            
        print(f"ADX >= {adx_th} | RSI [{rsi_low}, {rsi_high}] -> Trades: {tot_trades}, Total R: {tot_r:.2f}, R/trade: {(tot_r/tot_trades if tot_trades>0 else 0):.3f}")
