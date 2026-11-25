import pandas as pd
import numpy as np

def run_scalper_with_structural_stop(m5_path, h1_path, symbol_name, family, spread_points, tp2_rr=2.0):
    df_m5 = pd.read_csv(m5_path)
    df_m5['time'] = pd.to_datetime(df_m5['time'])
    df_m5 = df_m5.sort_values('time').reset_index(drop=True)
    
    df_h1 = pd.read_csv(h1_path)
    df_h1['time'] = pd.to_datetime(df_h1['time'])
    df_h1 = df_h1.sort_values('time').reset_index(drop=True)
    
    # H1 Trend & ATR
    df_h1['ema50'] = df_h1['close'].ewm(span=50, adjust=False).mean()
    df_h1['ema200'] = df_h1['close'].ewm(span=200, adjust=False).mean()
    
    tr_h1 = np.maximum(df_h1['high'].values[1:] - df_h1['low'].values[1:],
                       np.maximum(abs(df_h1['high'].values[1:] - df_h1['close'].values[:-1]),
                                  abs(df_h1['low'].values[1:] - df_h1['close'].values[:-1])))
    tr_h1 = np.insert(tr_h1, 0, df_h1['high'].iloc[0] - df_h1['low'].iloc[0])
    df_h1['atr_h1'] = pd.Series(tr_h1).rolling(14).mean().values
    df_h1['h1_close_time'] = df_h1['time'] + pd.Timedelta(hours=1)
    
    # Merge H1 cerrado a M5 (cero lookahead)
    m5 = pd.merge_asof(
        df_m5,
        df_h1[['h1_close_time', 'ema50', 'ema200', 'atr_h1']],
        left_on='time',
        right_on='h1_close_time',
        direction='backward'
    )
    
    n = len(m5)
    high = m5['high'].values
    low = m5['low'].values
    close = m5['close'].values
    open_p = m5['open'].values
    times = m5['time'].values
    
    # ATR M5 & ADX M5
    tr_m5 = np.maximum(high[1:] - low[1:], np.maximum(abs(high[1:] - close[:-1]), abs(low[1:] - close[:-1])))
    tr_m5 = np.insert(tr_m5, 0, high[0] - low[0])
    atr_m5 = pd.Series(tr_m5).rolling(14).mean().values
    
    up_move = high[1:] - high[:-1]
    down_move = low[:-1] - low[1:]
    plus_dm = np.where((up_move > down_move) & (up_move > 0), up_move, 0.0)
    minus_dm = np.where((down_move > up_move) & (down_move > 0), down_move, 0.0)
    plus_dm = np.insert(plus_dm, 0, 0.0)
    minus_dm = np.insert(minus_dm, 0, 0.0)
    
    atr_smooth = pd.Series(tr_m5).rolling(14).mean().values
    plus_di = 100.0 * pd.Series(plus_dm).rolling(14).mean().values / np.where(atr_smooth > 0, atr_smooth, 1.0)
    minus_di = 100.0 * pd.Series(minus_dm).rolling(14).mean().values / np.where(atr_smooth > 0, atr_smooth, 1.0)
    sum_di = plus_di + minus_di
    dx = 100.0 * np.abs(plus_di - minus_di) / np.where(sum_di > 0, sum_di, 1.0)
    adx14 = pd.Series(dx).rolling(14).mean().values
    
    trades = []
    in_trade = None
    pending_order = None
    
    SWING_WINDOW = 24
    MAX_PENDING_BARS = 6
    
    recent_sweep = None
    
    start_bar = 300
    for i in range(start_bar, n):
        c_time = times[i]
        c_high = high[i]
        c_low = low[i]
        c_close = close[i]
        c_open = open_p[i]
        c_atr_h1 = m5['atr_h1'].iloc[i] if (not np.isnan(m5['atr_h1'].iloc[i]) and m5['atr_h1'].iloc[i] > 0) else 10.0
        c_adx = adx14[i] if not np.isnan(adx14[i]) else 0.0
        
        # 1. Gestionar trade activo
        if in_trade is not None:
            direction = in_trade['direction']
            entry = in_trade['entry']
            sl = in_trade['sl']
            tp1 = in_trade['tp1']
            tp2 = in_trade['tp2']
            be_price = in_trade['be_price']
            leg1_closed = in_trade['leg1_closed']
            
            if direction == 'BUY':
                if not leg1_closed:
                    if c_low <= sl:
                        trades.append({'symbol': symbol_name, 'family': family, 'entry_time': in_trade['entry_time'],
                                       'exit_time': c_time, 'direction': direction, 'realized_r': -1.0, 'outcome': 'SL_FULL'})
                        in_trade = None
                    elif c_high >= tp1:
                        in_trade['leg1_closed'] = True
                        if c_high >= tp2:
                            trades.append({'symbol': symbol_name, 'family': family, 'entry_time': in_trade['entry_time'],
                                           'exit_time': c_time, 'direction': direction, 'realized_r': 0.5 * 1.0 + 0.5 * tp2_rr,
                                           'outcome': 'TP1_AND_TP2'})
                            in_trade = None
                else:
                    if c_low <= be_price:
                        trades.append({'symbol': symbol_name, 'family': family, 'entry_time': in_trade['entry_time'],
                                       'exit_time': c_time, 'direction': direction, 'realized_r': 0.50, 'outcome': 'TP1_THEN_BE'})
                        in_trade = None
                    elif c_high >= tp2:
                        trades.append({'symbol': symbol_name, 'family': family, 'entry_time': in_trade['entry_time'],
                                       'exit_time': c_time, 'direction': direction, 'realized_r': 0.5 * 1.0 + 0.5 * tp2_rr,
                                       'outcome': 'TP1_THEN_TP2'})
                        in_trade = None
            else: # SELL
                if not leg1_closed:
                    if c_high >= sl:
                        trades.append({'symbol': symbol_name, 'family': family, 'entry_time': in_trade['entry_time'],
                                       'exit_time': c_time, 'direction': direction, 'realized_r': -1.0, 'outcome': 'SL_FULL'})
                        in_trade = None
                    elif c_low <= tp1:
                        in_trade['leg1_closed'] = True
                        if c_low <= tp2:
                            trades.append({'symbol': symbol_name, 'family': family, 'entry_time': in_trade['entry_time'],
                                           'exit_time': c_time, 'direction': direction, 'realized_r': 0.5 * 1.0 + 0.5 * tp2_rr,
                                           'outcome': 'TP1_AND_TP2'})
                            in_trade = None
                else:
                    if c_high >= be_price:
                        trades.append({'symbol': symbol_name, 'family': family, 'entry_time': in_trade['entry_time'],
                                       'exit_time': c_time, 'direction': direction, 'realized_r': 0.50, 'outcome': 'TP1_THEN_BE'})
                        in_trade = None
                    elif c_low <= tp2:
                        trades.append({'symbol': symbol_name, 'family': family, 'entry_time': in_trade['entry_time'],
                                       'exit_time': c_time, 'direction': direction, 'realized_r': 0.5 * 1.0 + 0.5 * tp2_rr,
                                       'outcome': 'TP1_THEN_TP2'})
                        in_trade = None
            continue
            
        # 2. Gestionar orden pendiente
        if pending_order is not None:
            p = pending_order
            if i - p['placed_bar'] > MAX_PENDING_BARS:
                pending_order = None
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
                    if risk_dist >= 2.0 * spread_points:
                        in_trade = {
                            'direction': p['direction'], 'entry': actual_entry, 'sl': p['sl'],
                            'tp1': actual_entry + risk_dist if p['direction'] == 'BUY' else actual_entry - risk_dist,
                            'tp2': actual_entry + risk_dist * tp2_rr if p['direction'] == 'BUY' else actual_entry - risk_dist * tp2_rr,
                            'be_price': actual_entry + (spread_points * 0.5 if p['direction'] == 'BUY' else -spread_points * 0.5),
                            'leg1_closed': False, 'entry_time': c_time
                        }
                    pending_order = None
                    continue

        # 3. Filtro ADX de Momentum
        min_adx = 25.0 if family == 'STEP' else 20.0
        if c_adx < min_adx:
            continue
            
        h1_ema50 = m5['ema50'].iloc[i]
        if pd.isna(h1_ema50):
            continue
            
        local_swing_h = np.max(high[i - SWING_WINDOW:i])
        local_swing_l = np.min(low[i - SWING_WINDOW:i])
        
        bar_range = c_high - c_low
        if bar_range > 0:
            upper_wick = c_high - max(c_open, c_close)
            lower_wick = min(c_open, c_close) - c_low
            
            if c_high > local_swing_h and (upper_wick / bar_range) >= 0.20:
                recent_sweep = {'type': 'BEARISH_SWEEP', 'bar': i, 'peak': c_high}
            elif c_low < local_swing_l and (lower_wick / bar_range) >= 0.20:
                recent_sweep = {'type': 'BULLISH_SWEEP', 'bar': i, 'trough': c_low}
                
        if recent_sweep is not None:
            if i - recent_sweep['bar'] > 6:
                recent_sweep = None
            else:
                # Regla de Stop Loss Estructural: el SL debe cubrir al menos 0.85 ATR H1
                # para no morir con el drift previo al spike
                min_sl_dist = 0.85 * c_atr_h1
                
                # Caso VENTA (Crash, Step, Volatility)
                can_sell = (family in ['CRASH', 'STEP', 'VOLATILITY'])
                h1_bearish = (family == 'CRASH') or (c_close < h1_ema50)
                
                if can_sell and h1_bearish and recent_sweep['type'] == 'BEARISH_SWEEP':
                    if c_close < low[i-1] and low[i-2] > c_high:
                        fvg_ce = (low[i-2] + c_high) / 2.0
                        calc_sl = recent_sweep['peak'] + spread_points + 0.10 * c_atr_h1
                        if (calc_sl - fvg_ce) < min_sl_dist:
                            calc_sl = fvg_ce + min_sl_dist
                        pending_order = {
                            'direction': 'SELL', 'limit_price': fvg_ce, 'sl': calc_sl,
                            'placed_bar': i
                        }
                        recent_sweep = None
                        
                # Caso COMPRA (Boom, Step, Volatility)
                can_buy = (family in ['BOOM', 'STEP', 'VOLATILITY'])
                h1_bullish = (family == 'BOOM') or (c_close > h1_ema50)
                
                if can_buy and h1_bullish and recent_sweep and recent_sweep['type'] == 'BULLISH_SWEEP':
                    if c_close > high[i-1] and high[i-2] < c_low:
                        fvg_ce = (high[i-2] + c_low) / 2.0
                        calc_sl = recent_sweep['trough'] - spread_points - 0.10 * c_atr_h1
                        if (fvg_ce - calc_sl) < min_sl_dist:
                            calc_sl = fvg_ce - min_sl_dist
                        pending_order = {
                            'direction': 'BUY', 'limit_price': fvg_ce, 'sl': calc_sl,
                            'placed_bar': i
                        }
                        recent_sweep = None

    res_df = pd.DataFrame(trades)
    if len(res_df) == 0:
        return {'symbol': symbol_name, 'trades': 0}
        
    wins = res_df[res_df['realized_r'] > 0]
    losses = res_df[res_df['realized_r'] < 0]
    wr = len(wins) / len(res_df) * 100.0
    total_r = res_df['realized_r'].sum()
    gross_win = wins['realized_r'].sum()
    gross_loss = abs(losses['realized_r'].sum())
    pf = (gross_win / gross_loss) if gross_loss > 0 else np.inf
    
    # Balance $10k
    balance = 10000.0
    peak = 10000.0
    max_dd_pct = 0.0
    for r in res_df['realized_r']:
        risk_usd = balance * 0.01
        pnl = r * risk_usd
        balance += pnl
        if balance > peak:
            peak = balance
        dd = (peak - balance) / peak * 100.0
        if dd > max_dd_pct:
            max_dd_pct = dd
    gain_usd = balance - 10000.0
    gain_pct = gain_usd / 10000.0 * 100.0
    
    return {
        'symbol': symbol_name, 'family': family, 'trades': len(res_df), 'wr': wr, 'total_r': total_r,
        'pf': pf, 'max_dd_pct': max_dd_pct, 'gain_usd': gain_usd, 'gain_pct': gain_pct,
        'outcomes': res_df['outcome'].value_counts().to_dict()
    }

if __name__ == '__main__':
    targets = [
        ('data/historical/Crash_1000_Index_M5.csv', 'data/historical/Crash_1000_Index_H1.csv', 'Crash 1000 Index', 'CRASH', 0.5),
        ('data/historical/Boom_1000_Index_M5.csv', 'data/historical/Boom_1000_Index_H1.csv', 'Boom 1000 Index', 'BOOM', 1.0),
        ('data/historical/Step_Index_M5.csv', 'data/historical/Step_Index_H1.csv', 'Step Index', 'STEP', 2.0),
        ('data/historical/Volatility_75_Index_M5.csv', 'data/historical/Volatility_75_Index_H1.csv', 'Volatility 75 Index', 'VOLATILITY', 10.0),
        ('data/historical/Volatility_100_Index_M5.csv', 'data/historical/Volatility_100_Index_H1.csv', 'Volatility 100 Index', 'VOLATILITY', 5.0),
    ]
    for m5_p, h1_p, sym, fam, sp in targets:
        r = run_scalper_with_structural_stop(m5_p, h1_p, sym, fam, spread_points=sp)
        print(f"[{fam}] {sym} -> Trades: {r['trades']} | WR: {r['wr']:.1f}% | R: {r['total_r']:+.2f} R | PF: {r['pf']:.2f} | MaxDD: {r['max_dd_pct']:.2f}% | Ganancia: ${r['gain_usd']:+.2f} ({r['gain_pct']:+.1f}%)")
        print(f"      Outcomes: {r['outcomes']}\n")
