"""Deep dive reconciliation of Gold Quarters 422 trades across 4 chronological windows."""
import sys
from pathlib import Path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import pandas as pd
import numpy as np
from scratch.audit_gold_quarters_full import run_fast_gold_audit

# Let's run and capture the trades dataframe for min_rr = 1.5
def analyze_gold_windows():
    m5 = pd.read_csv(PROJECT_ROOT / 'data/historical/XAUUSD_M5.csv')
    h1 = pd.read_csv(PROJECT_ROOT / 'data/historical/XAUUSD_H1.csv')
    m5['time'] = pd.to_datetime(m5['time'], utc=True)
    h1['time'] = pd.to_datetime(h1['time'], utc=True)
    m5 = m5.sort_values('time').reset_index(drop=True)
    h1 = h1.sort_values('time').reset_index(drop=True)

    prev_close = m5['close'].shift(1)
    tr = pd.concat([m5['high'] - m5['low'], (m5['high'] - prev_close).abs(), (m5['low'] - prev_close).abs()], axis=1).max(axis=1)
    m5['atr'] = tr.rolling(14).mean().shift(1)
    h1['ema20'] = h1['close'].ewm(span=20, adjust=False).mean()
    h1['ema50'] = h1['close'].ewm(span=50, adjust=False).mean()

    m5_times = m5['time'].values
    h1_times = h1['time'].values
    m5_open = m5['open'].values
    m5_high = m5['high'].values
    m5_low = m5['low'].values
    m5_close = m5['close'].values
    m5_atr = m5['atr'].values
    h1_high = h1['high'].values
    h1_low = h1['low'].values
    h1_open = h1['open'].values
    h1_close = h1['close'].values
    h1_ema20 = h1['ema20'].values
    h1_ema50 = h1['ema50'].values

    first_h1_time = h1_times[25]
    start_idx = np.searchsorted(m5_times, first_h1_time, side='right') + 20
    min_rr = 1.5
    signals = []

    for i in range(start_idx, len(m5) - 50):
        atr_val = m5_atr[i]
        if np.isnan(atr_val) or atr_val <= 0: continue
        eff_tol = min(5.0, max(2.0, 0.10 * atr_val))
        span = m5_high[i-1] - m5_low[i-1]
        if span <= 0: continue
        entry_price = m5_close[i]
        sl_buffer = max(0.50 * atr_val, 4.0)
        
        rej_low = m5_low[i-1]
        q_low = round(rej_low / 25.0) * 25.0
        if abs(rej_low - q_low) <= eff_tol:
            wick = min(m5_open[i-1], m5_close[i-1]) - rej_low
            favorable = (m5_close[i-1] > q_low and m5_close[i] > m5_high[i-1] and m5_close[i] > m5_open[i])
            if wick / span >= 0.45 and favorable:
                t_eval = m5_times[i]
                cutoff = t_eval - np.timedelta64(1, 'h')
                h1_idx = np.searchsorted(h1_times, cutoff, side='right')
                if h1_idx >= 20:
                    h1_slice_high = h1_high[max(0, h1_idx - 100): h1_idx].max()
                    h1_slice_low = h1_low[max(0, h1_idx - 100): h1_idx].min()
                    mid = (h1_slice_high + h1_slice_low) / 2.0
                    if h1_slice_low <= entry_price < mid:
                        last_h1_bull = h1_close[h1_idx - 1] >= h1_open[h1_idx - 1]
                        ema20_val = h1_ema20[h1_idx - 1]
                        ema50_val = h1_ema50[h1_idx - 1]
                        if not (ema20_val < ema50_val and entry_price < ema20_val and not last_h1_bull):
                            stop = rej_low - sl_buffer
                            tp1 = q_low + 25.0
                            tp2 = q_low + 50.0
                            risk = entry_price - stop
                            if risk > 0 and (tp1 - entry_price) / risk >= min_rr:
                                signals.append({'idx': i, 'time': pd.Timestamp(m5_times[i]), 'direction': 'BUY', 'entry': entry_price, 'stop': stop, 'tp1': tp1, 'tp2': tp2, 'risk': risk})
                                continue

        rej_high = m5_high[i-1]
        q_high = round(rej_high / 25.0) * 25.0
        if abs(rej_high - q_high) <= eff_tol:
            wick = rej_high - max(m5_open[i-1], m5_close[i-1])
            favorable = (m5_close[i-1] < q_high and m5_close[i] < m5_low[i-1] and m5_close[i] < m5_open[i])
            if wick / span >= 0.45 and favorable:
                t_eval = m5_times[i]
                cutoff = t_eval - np.timedelta64(1, 'h')
                h1_idx = np.searchsorted(h1_times, cutoff, side='right')
                if h1_idx >= 20:
                    h1_slice_high = h1_high[max(0, h1_idx - 100): h1_idx].max()
                    h1_slice_low = h1_low[max(0, h1_idx - 100): h1_idx].min()
                    mid = (h1_slice_high + h1_slice_low) / 2.0
                    if mid < entry_price <= h1_slice_high:
                        last_h1_bear = h1_close[h1_idx - 1] <= h1_open[h1_idx - 1]
                        ema20_val = h1_ema20[h1_idx - 1]
                        ema50_val = h1_ema50[h1_idx - 1]
                        if not (ema20_val > ema50_val and entry_price > ema20_val and not last_h1_bear):
                            stop = rej_high + sl_buffer
                            tp1 = q_high - 25.0
                            tp2 = q_high - 50.0
                            risk = stop - entry_price
                            if risk > 0 and (entry_price - tp1) / risk >= min_rr:
                                signals.append({'idx': i, 'time': pd.Timestamp(m5_times[i]), 'direction': 'SELL', 'entry': entry_price, 'stop': stop, 'tp1': tp1, 'tp2': tp2, 'risk': risk})

    trades = []
    spread_usd = 0.30
    comm_usd = 0.06
    friction = spread_usd + comm_usd
    
    for s in signals:
        entry_i = s['idx'] + 1
        direction = s['direction']
        entry_price = s['entry']
        stop_loss = s['stop']
        tp1 = s['tp1']
        tp2 = s['tp2']
        risk = s['risk']
        
        future_slice = m5.iloc[entry_i: min(len(m5), entry_i + 72)]
        if future_slice.empty: continue
            
        be_active = False
        tp1_hit = False
        tp2_hit = False
        sl_hit = False
        leg1_r = -1.0
        leg2_r = -1.0
        
        for _, b in future_slice.iterrows():
            h = b['high']
            l = b['low']
            if direction == 'BUY':
                if (h - entry_price) / risk >= 1.0: be_active = True
                if h >= tp1 and not tp1_hit:
                    tp1_hit = True; leg1_r = (tp1 - entry_price - friction) / risk; be_active = True
                if h >= tp2 and not tp2_hit:
                    tp2_hit = True; leg2_r = (tp2 - entry_price - friction) / risk; break
                eff_sl = (entry_price + friction) if be_active else stop_loss
                if l <= eff_sl:
                    sl_hit = True
                    if not tp1_hit: leg1_r = 0.0 if be_active else -(risk + friction) / risk
                    leg2_r = 0.0 if be_active else -(risk + friction) / risk
                    break
            else:
                if (entry_price - l) / risk >= 1.0: be_active = True
                if l <= tp1 and not tp1_hit:
                    tp1_hit = True; leg1_r = (entry_price - tp1 - friction) / risk; be_active = True
                if l <= tp2 and not tp2_hit:
                    tp2_hit = True; leg2_r = (entry_price - tp2 - friction) / risk; break
                eff_sl = (entry_price - friction) if be_active else stop_loss
                if h >= eff_sl:
                    sl_hit = True
                    if not tp1_hit: leg1_r = 0.0 if be_active else -(risk + friction) / risk
                    leg2_r = 0.0 if be_active else -(risk + friction) / risk
                    break
                    
        if not sl_hit and not tp2_hit:
            last_c = future_slice.iloc[-1]['close']
            curr_r = (last_c - entry_price - friction)/risk if direction == 'BUY' else (entry_price - last_c - friction)/risk
            if not tp1_hit: leg1_r = curr_r if curr_r > 0 else (0.0 if be_active else -1.0)
            leg2_r = curr_r if curr_r > 0 else (0.0 if be_active else -1.0)
            
        net_r = 0.5 * leg1_r + 0.5 * leg2_r
        trades.append({
            'time': s['time'],
            'direction': direction,
            'entry': entry_price,
            'net_r': net_r,
            'win': 1 if net_r > 0 else 0
        })

    df_tr = pd.DataFrame(trades)
    print(f"Total trades: {len(df_tr)}")
    
    # Divide into 4 equal quartiles of 105-106 trades
    q1 = df_tr.iloc[:106]
    q2 = df_tr.iloc[106:212]
    q3 = df_tr.iloc[212:316]
    q4 = df_tr.iloc[316:] # The holdout (106 trades)
    
    quartiles = [("Q1 (Mayo 2025 - Sep 2025)", q1),
                 ("Q2 (Sep 2025 - Ene 2026)", q2),
                 ("Q3 (Ene 2026 - May 2026)", q3),
                 ("Q4 Holdout (May 2026 - Oct 2026)", q4)]
                 
    for name, q in quartiles:
        net = q['net_r'].sum()
        wr = q['win'].mean() * 100
        gw = q[q['net_r'] > 0]['net_r'].sum()
        gl = abs(q[q['net_r'] < 0]['net_r'].sum())
        pf = gw / gl if gl > 0 else float('inf')
        exp = net / len(q)
        print(f"\n{name}:")
        print(f"  Range: {q['time'].iloc[0]} -> {q['time'].iloc[-1]}")
        print(f"  Trades: {len(q)} | Net R: {net:+6.2f} R | WR: {wr:5.1f}% | PF: {pf:5.3f} | Exp: {exp:+6.4f} R/t")
        print(f"  Gold Price Range: {q['entry'].min():.1f} to {q['entry'].max():.1f}")
        buys = (q['direction'] == 'BUY').sum()
        sells = (q['direction'] == 'SELL').sum()
        print(f"  Buys: {buys}, Sells: {sells} | Buys Net: {q[q['direction']=='BUY']['net_r'].sum():+.2f} R, Sells Net: {q[q['direction']=='SELL']['net_r'].sum():+.2f} R")

if __name__ == '__main__':
    analyze_gold_windows()
