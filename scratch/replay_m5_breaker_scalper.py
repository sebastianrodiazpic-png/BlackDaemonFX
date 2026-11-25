import pandas as pd
import numpy as np

def run_scalping_breaker_retest(csv_path, symbol_name, spread_points=2.0, direction_filter=None):
    df = pd.read_csv(csv_path)
    df['time'] = pd.to_datetime(df['time'])
    df = df.sort_values('time').reset_index(drop=True)
    
    n_candles = len(df)
    
    high = df['high'].values
    low = df['low'].values
    close = df['close'].values
    open_p = df['open'].values
    
    # ATR M5 14
    tr = np.maximum(high[1:] - low[1:], np.maximum(abs(high[1:] - close[:-1]), abs(low[1:] - close[:-1])))
    tr = np.insert(tr, 0, high[0] - low[0])
    atr14 = pd.Series(tr).rolling(14).mean().values
    
    # EMA200 M5 como contexto de sesgo HTF (~16 horas)
    ema200 = pd.Series(close).ewm(span=200, adjust=False).mean().values
    
    trades = []
    in_trade = False
    
    # Breaker Retest Scalper:
    # 1. Identificar swing high/low previo de 12 velas
    # 2. Rompimiento claro (cierre de vela sobre swing high o bajo swing low)
    # 3. Retest del nivel roto dentro de las siguientes 15 velas
    # 4. Gatillo al cierre si hay vela de absorción (mecha >= 25% y cierre favorable)
    # 5. Entrada en la apertura de la vela siguiente
    
    LOOKBACK = 15
    active_breakers = [] # list of {'level': float, 'type': 'BULLISH'/'BEARISH', 'break_bar': int}
    
    i = 30
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

        # Limpiar breakers viejos (> 20 barras)
        active_breakers = [b for b in active_breakers if i - b['break_bar'] <= 20]
        
        c_open = open_p[i]
        c_close = close[i]
        c_high = high[i]
        c_low = low[i]
        c_atr = atr14[i] if atr14[i] > 0 else 1.0
        bar_range = c_high - c_low
        
        # 1. Detectar si la vela i rompe un swing previo de 12 velas
        local_swing_high = np.max(high[i - 12:i])
        local_swing_low = np.min(low[i - 12:i])
        
        if c_close > local_swing_high and open_p[i] <= local_swing_high:
            active_breakers.append({'level': local_swing_high, 'type': 'BULLISH', 'break_bar': i})
        elif c_close < local_swing_low and open_p[i] >= local_swing_low:
            active_breakers.append({'level': local_swing_low, 'type': 'BEARISH', 'break_bar': i})
            
        # 2. Evaluar si la vela i retestea algún breaker activo con mecha de absorción
        upper_wick = c_high - max(c_open, c_close)
        lower_wick = min(c_open, c_close) - c_low
        
        triggered = False
        for b in list(active_breakers):
            if i == b['break_bar']:
                continue
            lvl = b['level']
            b_type = b['type']
            
            # BUY RETEST
            if b_type == 'BULLISH' and (direction_filter is None or direction_filter == 'BUY') and c_close > ema200[i]:
                # El precio bajó a testear el nivel roto y rebotó hacia arriba
                if c_low <= lvl <= c_high and c_close > lvl:
                    if bar_range > 0 and (lower_wick / bar_range) >= 0.25 and c_close > c_open:
                        # Gatillo BUY confirmado: entrar en apertura de vela i+1
                        entry_price = open_p[i+1] + spread_points
                        sl_price = c_low - spread_points - (0.10 * c_atr)
                        risk_dist = abs(entry_price - sl_price)
                        if risk_dist >= 1.5 * spread_points:
                            in_trade = {
                                'direction': 'BUY', 'entry': entry_price, 'sl': sl_price,
                                'tp1': entry_price + risk_dist * 1.0,
                                'tp2': entry_price + risk_dist * 2.0,
                                'be_price': entry_price + spread_points,
                                'leg1_closed': False, 'entry_time': df['time'].iloc[i+1],
                            }
                            active_breakers.remove(b)
                            triggered = True
                            break
                            
            # SELL RETEST
            elif b_type == 'BEARISH' and (direction_filter is None or direction_filter == 'SELL') and c_close < ema200[i]:
                # El precio subió a testear el soporte roto y rebotó hacia abajo
                if c_low <= lvl <= c_high and c_close < lvl:
                    if bar_range > 0 and (upper_wick / bar_range) >= 0.25 and c_close < c_open:
                        entry_price = open_p[i+1] - spread_points
                        sl_price = c_high + spread_points + (0.10 * c_atr)
                        risk_dist = abs(entry_price - sl_price)
                        if risk_dist >= 1.5 * spread_points:
                            in_trade = {
                                'direction': 'SELL', 'entry': entry_price, 'sl': sl_price,
                                'tp1': entry_price - risk_dist * 1.0,
                                'tp2': entry_price - risk_dist * 2.0,
                                'be_price': entry_price - spread_points,
                                'leg1_closed': False, 'entry_time': df['time'].iloc[i+1],
                            }
                            active_breakers.remove(b)
                            triggered = True
                            break
        i += 1

    res_df = pd.DataFrame(trades)
    print(f"\n{'='*70}")
    print(f"REPLAY FIEL SCALPER BREAKER RETEST M5: {symbol_name} [{direction_filter or 'BIDIRECT'}]")
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
    print(res_df['outcome'].value_counts().to_string())
    
    half = len(res_df) // 2
    if half >= 20:
        part1 = res_df.iloc[:half]
        part2 = res_df.iloc[half:]
        r1, r2 = part1['realized_r'].sum(), part2['realized_r'].sum()
        wr1, wr2 = (part1['realized_r'] > 0).mean()*100, (part2['realized_r'] > 0).mean()*100
        print(f"Mitad 1 ({len(part1)} ops): {r1:+.2f} R (WR: {wr1:.1f}%)")
        print(f"Mitad 2 ({len(part2)} ops): {r2:+.2f} R (WR: {wr2:.1f}%)")
        print(f"Validación 2 Mitades: {'POSITIVO EN AMBAS (APROBADO)' if r1 > 0 and r2 > 0 else 'FALLA EN UNA MITAD'}")
    return res_df

# Run across the key assets
run_scalping_breaker_retest('data/historical/Crash_1000_Index_M5.csv', 'Crash 1000 Index', spread_points=0.5, direction_filter='SELL')
run_scalping_breaker_retest('data/historical/Boom_1000_Index_M5.csv', 'Boom 1000 Index', spread_points=1.0, direction_filter='BUY')
run_scalping_breaker_retest('data/historical/Step_Index_M5.csv', 'Step Index', spread_points=2.0, direction_filter=None)
run_scalping_breaker_retest('data/historical/Volatility_75_Index_M5.csv', 'Volatility 75 Index', spread_points=10.0, direction_filter=None)
