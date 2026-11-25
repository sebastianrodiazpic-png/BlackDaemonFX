import pandas as pd
import numpy as np

def run_scalping_replay_htf(csv_path, symbol_name, spread_points=2.0, direction_filter=None):
    df = pd.read_csv(csv_path)
    df['time'] = pd.to_datetime(df['time'])
    df = df.sort_values('time').reset_index(drop=True)
    
    n_candles = len(df)
    
    high = df['high'].values
    low = df['low'].values
    close = df['close'].values
    open_p = df['open'].values
    
    # Simular H1 EMA50 sobre M5 (50 barras H1 = 600 barras M5)
    ema_h1 = pd.Series(close).ewm(span=600, adjust=False).mean().values
    
    trades = []
    in_trade = False
    pending_limit = None
    
    SWING_WINDOW = 24  # 2 horas de swing local en M5
    MAX_PENDING_BARS = 6
    
    i = SWING_WINDOW + 3
    while i < n_candles - 1:
        if in_trade:
            pos = in_trade
            c_high = high[i]
            c_low = low[i]
            c_time = df['time'].iloc[i]
            
            direction = pos['direction']
            entry = pos['entry']
            sl = pos['sl']
            tp1 = pos['tp1']
            tp2 = pos['tp2']
            be_price = pos['be_price']
            leg1_closed = pos['leg1_closed']
            
            if direction == 'BUY':
                if not leg1_closed:
                    if c_low <= sl:
                        trades.append({'symbol': symbol_name, 'entry_time': pos['entry_time'], 'exit_time': c_time,
                                       'direction': direction, 'realized_r': -1.0, 'outcome': 'SL_FULL'})
                        in_trade = False
                    elif c_high >= tp1:
                        pos['leg1_closed'] = True
                        if c_high >= tp2:
                            trades.append({'symbol': symbol_name, 'entry_time': pos['entry_time'], 'exit_time': c_time,
                                           'direction': direction, 'realized_r': 1.5, 'outcome': 'TP1_AND_TP2'})
                            in_trade = False
                else:
                    if c_low <= be_price:
                        trades.append({'symbol': symbol_name, 'entry_time': pos['entry_time'], 'exit_time': c_time,
                                       'direction': direction, 'realized_r': 0.5, 'outcome': 'TP1_THEN_BE'})
                        in_trade = False
                    elif c_high >= tp2:
                        trades.append({'symbol': symbol_name, 'entry_time': pos['entry_time'], 'exit_time': c_time,
                                       'direction': direction, 'realized_r': 1.5, 'outcome': 'TP1_THEN_TP2'})
                        in_trade = False
            else: # SELL
                if not leg1_closed:
                    if c_high >= sl:
                        trades.append({'symbol': symbol_name, 'entry_time': pos['entry_time'], 'exit_time': c_time,
                                       'direction': direction, 'realized_r': -1.0, 'outcome': 'SL_FULL'})
                        in_trade = False
                    elif c_low <= tp1:
                        pos['leg1_closed'] = True
                        if c_low <= tp2:
                            trades.append({'symbol': symbol_name, 'entry_time': pos['entry_time'], 'exit_time': c_time,
                                           'direction': direction, 'realized_r': 1.5, 'outcome': 'TP1_AND_TP2'})
                            in_trade = False
                else:
                    if c_high >= be_price:
                        trades.append({'symbol': symbol_name, 'entry_time': pos['entry_time'], 'exit_time': c_time,
                                       'direction': direction, 'realized_r': 0.5, 'outcome': 'TP1_THEN_BE'})
                        in_trade = False
                    elif c_low <= tp2:
                        trades.append({'symbol': symbol_name, 'entry_time': pos['entry_time'], 'exit_time': c_time,
                                       'direction': direction, 'realized_r': 1.5, 'outcome': 'TP1_THEN_TP2'})
                        in_trade = False
            i += 1
            continue

        if pending_limit:
            p = pending_limit
            c_high = high[i]
            c_low = low[i]
            if i - p['placed_bar'] > MAX_PENDING_BARS:
                pending_limit = None
            else:
                filled = False
                if p['direction'] == 'BUY' and c_low <= p['limit_price']:
                    filled = True
                    actual_entry = p['limit_price'] + spread_points
                elif p['direction'] == 'SELL' and c_high >= p['limit_price']:
                    filled = True
                    actual_entry = p['limit_price'] - spread_points
                    
                if filled:
                    risk_dist = abs(actual_entry - p['sl'])
                    if risk_dist > 1.2 * spread_points:
                        in_trade = {
                            'direction': p['direction'], 'entry': actual_entry, 'sl': p['sl'],
                            'tp1': actual_entry + risk_dist * 1.0 if p['direction'] == 'BUY' else actual_entry - risk_dist * 1.0,
                            'tp2': actual_entry + risk_dist * 2.0 if p['direction'] == 'BUY' else actual_entry - risk_dist * 2.0,
                            'be_price': actual_entry + (spread_points if p['direction'] == 'BUY' else -spread_points),
                            'leg1_closed': False, 'entry_time': df['time'].iloc[i],
                        }
                    pending_limit = None
                    i += 1
                    continue

        local_swing_high = np.max(high[i - SWING_WINDOW:i])
        local_swing_low = np.min(low[i - SWING_WINDOW:i])
        
        c_open = open_p[i]
        c_close = close[i]
        c_high = high[i]
        c_low = low[i]
        bar_range = c_high - c_low
        body = abs(c_close - c_open)
        
        # Filtro de rechazo / absorción institucional: mecha de rechazo >= 25% del rango
        upper_wick = c_high - max(c_open, c_close)
        lower_wick = min(c_open, c_close) - c_low
        
        h1_trend_bull = c_close > ema_h1[i]
        h1_trend_bear = c_close < ema_h1[i]
        
        # BEARISH SCALP (SELL)
        if (direction_filter is None or direction_filter == 'SELL') and h1_trend_bear:
            if bar_range > 0 and (upper_wick / bar_range) >= 0.25 and (body / bar_range) >= 0.35:
                if high[i-1] >= local_swing_high or c_high >= local_swing_high:
                    if c_close < c_open and c_close < low[i-1]:
                        if low[i-2] > c_high:  # FVG
                            fvg_ce = (low[i-2] + c_high) / 2.0
                            pending_limit = {
                                'direction': 'SELL',
                                'limit_price': fvg_ce,
                                'sl': max(c_high, high[i-1]) + spread_points,
                                'placed_bar': i,
                                'signal_time': df['time'].iloc[i],
                            }

        # BULLISH SCALP (BUY)
        if (direction_filter is None or direction_filter == 'BUY') and h1_trend_bull:
            if bar_range > 0 and (lower_wick / bar_range) >= 0.25 and (body / bar_range) >= 0.35:
                if low[i-1] <= local_swing_low or c_low <= local_swing_low:
                    if c_close > c_open and c_close > high[i-1]:
                        if high[i-2] < c_low:  # FVG
                            fvg_ce = (high[i-2] + c_low) / 2.0
                            pending_limit = {
                                'direction': 'BUY',
                                'limit_price': fvg_ce,
                                'sl': min(c_low, low[i-1]) - spread_points,
                                'placed_bar': i,
                                'signal_time': df['time'].iloc[i],
                            }
        i += 1

    res_df = pd.DataFrame(trades)
    print(f"\n{'='*70}")
    print(f"REPLAY FIEL SCALPING CONFLUENTE (HTF + ABSORPTION WICK): {symbol_name} [{direction_filter or 'BIDIRECT'}]")
    print(f"{'='*70}")
    if len(res_df) == 0:
        print("0 trades.")
        return None
        
    wins = res_df[res_df['realized_r'] > 0]
    losses = res_df[res_df['realized_r'] < 0]
    wr = len(wins) / len(res_df) * 100
    total_r = res_df['realized_r'].sum()
    avg_r = res_df['realized_r'].mean()
    gross_win = wins['realized_r'].sum()
    gross_loss = abs(losses['realized_r'].sum())
    pf = (gross_win / gross_loss) if gross_loss > 0 else np.inf
    
    print(f"Total trades: {len(res_df)} | WR: {wr:.2f}% | R Neto: {total_r:+.2f} R | R/trade: {avg_r:+.3f} R | PF: {pf:.2f}")
    
    half = len(res_df) // 2
    if half >= 20:
        part1 = res_df.iloc[:half]
        part2 = res_df.iloc[half:]
        r1, r2 = part1['realized_r'].sum(), part2['realized_r'].sum()
        wr1, wr2 = (part1['realized_r'] > 0).mean()*100, (part2['realized_r'] > 0).mean()*100
        print(f"Mitad 1 ({len(part1)} ops): {r1:+.2f} R (WR: {wr1:.1f}%)")
        print(f"Mitad 2 ({len(part2)} ops): {r2:+.2f} R (WR: {wr2:.1f}%)")
        print(f"Validación 2 Mitades: {'POSITIVO EN AMBAS' if r1 > 0 and r2 > 0 else 'FALLA EN AL MENOS UNA'}")
    return res_df

# Evaluate on Crash 1000 SELL, Boom 1000 BUY, Step Index
run_scalping_replay_htf('data/historical/Crash_1000_Index_M5.csv', 'Crash 1000 Index', spread_points=0.5, direction_filter='SELL')
run_scalping_replay_htf('data/historical/Boom_1000_Index_M5.csv', 'Boom 1000 Index', spread_points=1.0, direction_filter='BUY')
run_scalping_replay_htf('data/historical/Step_Index_M5.csv', 'Step Index', spread_points=2.0, direction_filter=None)
run_scalping_replay_htf('data/historical/Volatility_75_Index_M5.csv', 'Volatility 75 Index', spread_points=10.0, direction_filter=None)
