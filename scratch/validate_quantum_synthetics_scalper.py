import pandas as pd
import numpy as np

def run_qss_replay(csv_path, symbol_name, family, spread_points=1.0):
    df = pd.read_csv(csv_path)
    df['time'] = pd.to_datetime(df['time'])
    df = df.sort_values('time').reset_index(drop=True)
    n = len(df)
    
    high = df['high'].values
    low = df['low'].values
    close = df['close'].values
    open_p = df['open'].values
    
    # 1. PILAR 1: H1 Trend Context (50 barras H1 = 600 barras M5)
    ema_h1 = pd.Series(close).ewm(span=600, adjust=False).mean().values
    
    # ATR M5 14
    tr = np.maximum(high[1:] - low[1:], np.maximum(abs(high[1:] - close[:-1]), abs(low[1:] - close[:-1])))
    tr = np.insert(tr, 0, high[0] - low[0])
    atr14 = pd.Series(tr).rolling(14).mean().values
    
    # 2. PILAR 2: ADX M5/H1 proxy (Fuerza direccional)
    up_move = high[1:] - high[:-1]
    down_move = low[:-1] - low[1:]
    plus_dm = np.where((up_move > down_move) & (up_move > 0), up_move, 0.0)
    minus_dm = np.where((down_move > up_move) & (down_move > 0), down_move, 0.0)
    plus_dm = np.insert(plus_dm, 0, 0.0)
    minus_dm = np.insert(minus_dm, 0, 0.0)
    
    atr_smooth = pd.Series(tr).rolling(14).mean().values
    plus_di = 100.0 * pd.Series(plus_dm).rolling(14).mean().values / np.where(atr_smooth>0, atr_smooth, 1.0)
    minus_di = 100.0 * pd.Series(minus_dm).rolling(14).mean().values / np.where(atr_smooth>0, atr_smooth, 1.0)
    dx = 100.0 * np.abs(plus_di - minus_di) / np.where((plus_di + minus_di)>0, (plus_di + minus_di), 1.0)
    adx14 = pd.Series(dx).rolling(14).mean().values
    
    # Reglas por Familia de Sintéticos:
    # CRASH: SELL ONLY, aprovecha la asimetría de spikes bajistas
    # BOOM: BUY ONLY, aprovecha la asimetría de spikes alcistas
    # STEP: Bidireccional pero exige ADX >= 28.0 (alta expansión)
    # VOLATILITY: Bidireccional según H1 EMA, ADX >= 22.0
    
    trades = []
    in_trade = False
    pending_limit = None
    
    SWING_WINDOW = 24  # 2 horas de swing local en M5
    MAX_PENDING_BARS = 6
    
    i = 650  # Permitir warmup de EMA H1
    while i < n - 1:
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
                    if risk_dist >= 1.5 * spread_points:
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

        c_open = open_p[i]
        c_close = close[i]
        c_high = high[i]
        c_low = low[i]
        c_atr = atr14[i] if atr14[i] > 0 else 1.0
        bar_range = c_high - c_low
        body = abs(c_close - c_open)
        upper_wick = c_high - max(c_open, c_close)
        lower_wick = min(c_open, c_close) - c_low
        
        # Filtros de Admisión Cuantitativa
        adx_val = adx14[i] if not np.isnan(adx14[i]) else 20.0
        min_adx = 28.0 if family == 'STEP' else (22.0 if family == 'VOLATILITY' else 18.0)
        adx_ok = adx_val >= min_adx
        
        local_swing_high = np.max(high[i - SWING_WINDOW:i])
        local_swing_low = np.min(low[i - SWING_WINDOW:i])
        
        # --- CASO VENTA (SELL) ---
        can_sell = family in ['CRASH', 'STEP', 'VOLATILITY']
        h1_bearish = c_close < ema_h1[i]
        if can_sell and h1_bearish and adx_ok:
            # Sweep de liquidez M5
            swept_high = high[i-1] >= local_swing_high or c_high >= local_swing_high
            # Vela de absorción: mecha superior >= 25% y cuerpo desplazando hacia abajo
            absorb_ok = bar_range > 0 and (upper_wick / bar_range) >= 0.25 and c_close < c_open
            if swept_high and absorb_ok and c_close < low[i-1]:
                # FVG bajista
                if low[i-2] > c_high:
                    fvg_ce = (low[i-2] + c_high) / 2.0
                    sl_level = max(c_high, high[i-1]) + spread_points + (0.10 * c_atr)
                    pending_limit = {
                        'direction': 'SELL', 'limit_price': fvg_ce, 'sl': sl_level,
                        'placed_bar': i, 'signal_time': df['time'].iloc[i],
                    }

        # --- CASO COMPRA (BUY) ---
        can_buy = family in ['BOOM', 'STEP', 'VOLATILITY']
        h1_bullish = c_close > ema_h1[i]
        if can_buy and h1_bullish and adx_ok:
            swept_low = low[i-1] <= local_swing_low or c_low <= local_swing_low
            absorb_ok = bar_range > 0 and (lower_wick / bar_range) >= 0.25 and c_close > c_open
            if swept_low and absorb_ok and c_close > high[i-1]:
                # FVG alcista
                if high[i-2] < c_low:
                    fvg_ce = (high[i-2] + c_low) / 2.0
                    sl_level = min(c_low, low[i-1]) - spread_points - (0.10 * c_atr)
                    pending_limit = {
                        'direction': 'BUY', 'limit_price': fvg_ce, 'sl': sl_level,
                        'placed_bar': i, 'signal_time': df['time'].iloc[i],
                    }
        i += 1

    res_df = pd.DataFrame(trades)
    print(f"\n{'='*75}")
    print(f"REPLAY FIEL: QUANTUM SYNTHETICS SCALPER (QSS-4P) -> {symbol_name} [{family}]")
    print(f"{'='*75}")
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
    if half >= 10:
        part1 = res_df.iloc[:half]
        part2 = res_df.iloc[half:]
        r1, r2 = part1['realized_r'].sum(), part2['realized_r'].sum()
        wr1, wr2 = (part1['realized_r'] > 0).mean()*100, (part2['realized_r'] > 0).mean()*100
        print(f"\n--- VALIDACIÓN EN DOS MITADES ---")
        print(f"Mitad 1 ({len(part1)} ops): {r1:+.2f} R (WR: {wr1:.1f}%)")
        print(f"Mitad 2 ({len(part2)} ops): {r2:+.2f} R (WR: {wr2:.1f}%)")
        print(f"Estado de Validación: {'APROBADO (POSITIVO EN AMBAS)' if r1 > 0 and r2 > 0 else 'NO APROBADO'}")
    return res_df

# Run across all 4 key families
run_qss_replay('data/historical/Crash_1000_Index_M5.csv', 'Crash 1000 Index', family='CRASH', spread_points=0.5)
run_qss_replay('data/historical/Boom_1000_Index_M5.csv', 'Boom 1000 Index', family='BOOM', spread_points=1.0)
run_qss_replay('data/historical/Step_Index_M5.csv', 'Step Index', family='STEP', spread_points=2.0)
run_qss_replay('data/historical/Volatility_75_Index_M5.csv', 'Volatility 75 Index', family='VOLATILITY', spread_points=10.0)
