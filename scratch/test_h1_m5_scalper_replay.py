import pandas as pd
import numpy as np

def run_h1_m5_institutional_scalper(h1_csv, m5_csv, symbol, family, spread_points, tp2_mult=2.0):
    df_h1 = pd.read_csv(h1_csv)
    df_h1['time'] = pd.to_datetime(df_h1['time'])
    df_h1 = df_h1.sort_values('time').reset_index(drop=True)
    
    df_m5 = pd.read_csv(m5_csv)
    df_m5['time'] = pd.to_datetime(df_m5['time'])
    df_m5 = df_m5.sort_values('time').reset_index(drop=True)
    
    # 1. Procesar H1: Trend, ATR, ADX y Zonas Clave (High/Low de swing H1)
    df_h1['ema50'] = df_h1['close'].ewm(span=50, adjust=False).mean()
    df_h1['ema200'] = df_h1['close'].ewm(span=200, adjust=False).mean()
    
    tr_h1 = np.maximum(df_h1['high'].values[1:] - df_h1['low'].values[1:],
                       np.maximum(abs(df_h1['high'].values[1:] - df_h1['close'].values[:-1]),
                                  abs(df_h1['low'].values[1:] - df_h1['close'].values[:-1])))
    tr_h1 = np.insert(tr_h1, 0, df_h1['high'].iloc[0] - df_h1['low'].iloc[0])
    df_h1['atr14'] = pd.Series(tr_h1).rolling(14).mean().values
    
    # Merge asof: asociar a cada vela M5 el estado H1 CERRADO anterior (sin lookahead)
    # Una vela H1 a las 10:00 se cierra a las 11:00. Por lo tanto, para una vela M5 a las 10:25,
    # el último H1 CERRADO es el de las 09:00 (cerrado a las 10:00).
    df_h1['h1_closed_time'] = df_h1['time'] + pd.Timedelta(hours=1)
    
    # Marcamos zonas H1: Swing High / Low de las últimas 20 barras H1
    df_h1['h1_swing_high'] = df_h1['high'].rolling(20).max()
    df_h1['h1_swing_low'] = df_h1['low'].rolling(20).min()
    
    # H1 FVG
    df_h1['h1_bearish_fvg_top'] = np.where(df_h1['low'].shift(2) > df_h1['high'], df_h1['low'].shift(2), np.nan)
    df_h1['h1_bearish_fvg_bot'] = np.where(df_h1['low'].shift(2) > df_h1['high'], df_h1['high'], np.nan)
    df_h1['h1_bullish_fvg_top'] = np.where(df_h1['high'].shift(2) < df_h1['low'], df_h1['low'], np.nan)
    df_h1['h1_bullish_fvg_bot'] = np.where(df_h1['high'].shift(2) < df_h1['low'], df_h1['high'], np.nan)
    
    # M5 data
    m5_merged = pd.merge_asof(
        df_m5,
        df_h1[['h1_closed_time', 'ema50', 'ema200', 'atr14', 'h1_swing_high', 'h1_swing_low',
               'h1_bearish_fvg_top', 'h1_bearish_fvg_bot', 'h1_bullish_fvg_top', 'h1_bullish_fvg_bot']],
        left_on='time',
        right_on='h1_closed_time',
        direction='backward'
    )
    
    n = len(m5_merged)
    high = m5_merged['high'].values
    low = m5_merged['low'].values
    close = m5_merged['close'].values
    open_p = m5_merged['open'].values
    
    # ATR M5
    tr_m5 = np.maximum(high[1:] - low[1:], np.maximum(abs(high[1:] - close[:-1]), abs(low[1:] - close[:-1])))
    tr_m5 = np.insert(tr_m5, 0, high[0] - low[0])
    atr_m5 = pd.Series(tr_m5).rolling(14).mean().values
    
    trades = []
    in_trade = None
    pending_order = None
    MAX_PENDING_BARS = 6
    
    # Filtro direccional por familia
    # Crash: SELL ONLY
    # Boom: BUY ONLY
    # Step / Volatility: Segun H1 EMA50 vs EMA200
    
    start_bar = 500
    for i in range(start_bar, n):
        c_time = m5_merged['time'].iloc[i]
        c_high = high[i]
        c_low = low[i]
        c_close = close[i]
        c_open = open_p[i]
        c_atr = atr_m5[i] if atr_m5[i] > 0 else 1.0
        
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
                        trades.append({'symbol': symbol, 'entry_time': in_trade['entry_time'], 'exit_time': c_time,
                                       'direction': direction, 'realized_r': -1.0, 'outcome': 'SL_FULL'})
                        in_trade = None
                    elif c_high >= tp1:
                        in_trade['leg1_closed'] = True
                        if c_high >= tp2:
                            trades.append({'symbol': symbol, 'entry_time': in_trade['entry_time'], 'exit_time': c_time,
                                           'direction': direction, 'realized_r': 0.5 * 1.0 + 0.5 * tp2_mult, 'outcome': 'TP1_AND_TP2'})
                            in_trade = None
                else:
                    if c_low <= be_price:
                        trades.append({'symbol': symbol, 'entry_time': in_trade['entry_time'], 'exit_time': c_time,
                                       'direction': direction, 'realized_r': 0.50, 'outcome': 'TP1_THEN_BE'})
                        in_trade = None
                    elif c_high >= tp2:
                        trades.append({'symbol': symbol, 'entry_time': in_trade['entry_time'], 'exit_time': c_time,
                                       'direction': direction, 'realized_r': 0.5 * 1.0 + 0.5 * tp2_mult, 'outcome': 'TP1_THEN_TP2'})
                        in_trade = None
            else: # SELL
                if not leg1_closed:
                    if c_high >= sl:
                        trades.append({'symbol': symbol, 'entry_time': in_trade['entry_time'], 'exit_time': c_time,
                                       'direction': direction, 'realized_r': -1.0, 'outcome': 'SL_FULL'})
                        in_trade = None
                    elif c_low <= tp1:
                        in_trade['leg1_closed'] = True
                        if c_low <= tp2:
                            trades.append({'symbol': symbol, 'entry_time': in_trade['entry_time'], 'exit_time': c_time,
                                           'direction': direction, 'realized_r': 0.5 * 1.0 + 0.5 * tp2_mult, 'outcome': 'TP1_AND_TP2'})
                            in_trade = None
                else:
                    if c_high >= be_price:
                        trades.append({'symbol': symbol, 'entry_time': in_trade['entry_time'], 'exit_time': c_time,
                                       'direction': direction, 'realized_r': 0.50, 'outcome': 'TP1_THEN_BE'})
                        in_trade = None
                    elif c_low <= tp2:
                        trades.append({'symbol': symbol, 'entry_time': in_trade['entry_time'], 'exit_time': c_time,
                                       'direction': direction, 'realized_r': 0.5 * 1.0 + 0.5 * tp2_mult, 'outcome': 'TP1_THEN_TP2'})
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
                            'tp2': actual_entry + risk_dist * tp2_mult if p['direction'] == 'BUY' else actual_entry - risk_dist * tp2_mult,
                            'be_price': actual_entry + (spread_points * 0.5 if p['direction'] == 'BUY' else -spread_points * 0.5),
                            'leg1_closed': False, 'entry_time': c_time
                        }
                    pending_order = None
                    continue

        # 3. Setup de Entrada:
        # H1 Bias
        h1_ema50 = m5_merged['ema50'].iloc[i]
        h1_ema200 = m5_merged['ema200'].iloc[i]
        if pd.isna(h1_ema50) or pd.isna(h1_ema200):
            continue
            
        # SELL SETUP (Crash, Step, Volatility)
        can_sell = family in ['CRASH', 'STEP', 'VOLATILITY']
        h1_bearish = (family == 'CRASH') or (h1_ema50 < h1_ema200 and c_close < h1_ema50)
        
        if can_sell and h1_bearish:
            # M5 Trigger: Sweep de liquidez de las ultimas 12 barras M5 (1 hora)
            local_high = np.max(high[i-12:i])
            swept = c_high > local_high or high[i-1] > local_high
            # Vela de absorción o rechazo en M5: mecha superior >= 35% del rango total de la vela
            bar_range = c_high - c_low
            upper_wick = c_high - max(c_open, c_close)
            is_rejection = bar_range > 0 and (upper_wick / bar_range) >= 0.35 and c_close < c_open
            
            # FVG bajista en M5 tras el sweep
            if swept and is_rejection and low[i-2] > c_high:
                fvg_ce = (low[i-2] + c_high) / 2.0
                sl_level = max(c_high, high[i-1]) + spread_points + (0.15 * c_atr)
                pending_order = {
                    'direction': 'SELL', 'limit_price': fvg_ce, 'sl': sl_level,
                    'placed_bar': i
                }

        # BUY SETUP (Boom, Step, Volatility)
        can_buy = family in ['BOOM', 'STEP', 'VOLATILITY']
        h1_bullish = (family == 'BOOM') or (h1_ema50 > h1_ema200 and c_close > h1_ema50)
        
        if can_buy and h1_bullish:
            local_low = np.min(low[i-12:i])
            swept = c_low < local_low or low[i-1] < local_low
            bar_range = c_high - c_low
            lower_wick = min(c_open, c_close) - c_low
            is_rejection = bar_range > 0 and (lower_wick / bar_range) >= 0.35 and c_close > c_open
            
            if swept and is_rejection and high[i-2] < c_low:
                fvg_ce = (high[i-2] + c_low) / 2.0
                sl_level = min(c_low, low[i-1]) - spread_points - (0.15 * c_atr)
                pending_order = {
                    'direction': 'BUY', 'limit_price': fvg_ce, 'sl': sl_level,
                    'placed_bar': i
                }

    res_df = pd.DataFrame(trades)
    print(f"\n{'='*75}")
    print(f"REPLAY INSTITUCIONAL H1-M5: {symbol} [{family}]")
    print(f"{'='*75}")
    if len(res_df) == 0:
        print("0 trades ejecutados.")
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
    if half >= 5:
        part1 = res_df.iloc[:half]
        part2 = res_df.iloc[half:]
        r1, r2 = part1['realized_r'].sum(), part2['realized_r'].sum()
        wr1, wr2 = (part1['realized_r'] > 0).mean()*100, (part2['realized_r'] > 0).mean()*100
        print(f"\n--- VALIDACIÓN EN DOS MITADES ---")
        print(f"Mitad 1 ({len(part1)} ops): {r1:+.2f} R (WR: {wr1:.1f}%)")
        print(f"Mitad 2 ({len(part2)} ops): {r2:+.2f} R (WR: {wr2:.1f}%)")
        print(f"Estado de Validación: {'APROBADO (POSITIVO EN AMBAS)' if r1 > 0 and r2 > 0 else 'NO APROBADO'}")
    return res_df

if __name__ == '__main__':
    run_h1_m5_institutional_scalper('data/historical/Crash_1000_Index_H1.csv', 'data/historical/Crash_1000_Index_M5.csv', 'Crash 1000 Index', 'CRASH', spread_points=0.5)
    run_h1_m5_institutional_scalper('data/historical/Boom_1000_Index_H1.csv', 'data/historical/Boom_1000_Index_M5.csv', 'Boom 1000 Index', 'BOOM', spread_points=1.0)
    run_h1_m5_institutional_scalper('data/historical/Step_Index_H1.csv', 'data/historical/Step_Index_M5.csv', 'Step Index', 'STEP', spread_points=2.0)
    run_h1_m5_institutional_scalper('data/historical/Volatility_75_Index_H1.csv', 'data/historical/Volatility_75_Index_M5.csv', 'Volatility 75 Index', 'VOLATILITY', spread_points=10.0)
