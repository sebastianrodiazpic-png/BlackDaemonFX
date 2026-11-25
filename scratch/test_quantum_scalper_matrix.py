import pandas as pd
import numpy as np

def run_scalper_backtest(csv_path, symbol, family, spread_points, tp2_mult=2.5, adx_threshold=22.0):
    df = pd.read_csv(csv_path)
    df['time'] = pd.to_datetime(df['time'])
    df = df.sort_values('time').reset_index(drop=True)
    n = len(df)
    
    high = df['high'].values
    low = df['low'].values
    close = df['close'].values
    open_p = df['open'].values
    
    # 1. Indicadores Cuantitativos
    # EMA 200 M5 (~16 horas de tendencia intradía) y EMA 600 (~50 horas H1)
    ema_fast = pd.Series(close).ewm(span=200, adjust=False).mean().values
    ema_slow = pd.Series(close).ewm(span=600, adjust=False).mean().values
    
    # ATR 14 M5
    tr = np.maximum(high[1:] - low[1:], np.maximum(abs(high[1:] - close[:-1]), abs(low[1:] - close[:-1])))
    tr = np.insert(tr, 0, high[0] - low[0])
    atr14 = pd.Series(tr).rolling(14).mean().values
    
    # ADX 14
    up_move = high[1:] - high[:-1]
    down_move = low[:-1] - low[1:]
    plus_dm = np.where((up_move > down_move) & (up_move > 0), up_move, 0.0)
    minus_dm = np.where((down_move > up_move) & (down_move > 0), down_move, 0.0)
    plus_dm = np.insert(plus_dm, 0, 0.0)
    minus_dm = np.insert(minus_dm, 0, 0.0)
    
    atr_smooth = pd.Series(tr).rolling(14).mean().values
    plus_di = 100.0 * pd.Series(plus_dm).rolling(14).mean().values / np.where(atr_smooth > 0, atr_smooth, 1.0)
    minus_di = 100.0 * pd.Series(minus_dm).rolling(14).mean().values / np.where(atr_smooth > 0, atr_smooth, 1.0)
    dx = 100.0 * np.abs(plus_di - minus_di) / np.where((plus_di + minus_di) > 0, (plus_di + minus_di), 1.0)
    adx14 = pd.Series(dx).rolling(14).mean().values
    
    SWING_LOOKBACK = 20
    MAX_PENDING_BARS = 8
    
    trades = []
    in_trade = None
    pending_order = None
    
    # Estado de Liquidity Sweep
    recent_sweep_high = None  # {'bar': idx, 'price': float}
    recent_sweep_low = None
    
    start_bar = 650
    for i in range(start_bar, n):
        # 1. Gestionar Trade Activo
        if in_trade is not None:
            c_high = high[i]
            c_low = low[i]
            c_time = df['time'].iloc[i]
            direction = in_trade['direction']
            entry = in_trade['entry']
            sl = in_trade['sl']
            tp1 = in_trade['tp1']
            tp2 = in_trade['tp2']
            be_price = in_trade['be_price']
            leg1_closed = in_trade['leg1_closed']
            risk_dist = in_trade['risk_dist']
            
            if direction == 'BUY':
                if not leg1_closed:
                    if c_low <= sl:
                        trades.append({'symbol': symbol, 'family': family, 'entry_time': in_trade['entry_time'],
                                       'exit_time': c_time, 'direction': direction, 'realized_r': -1.0,
                                       'outcome': 'SL_FULL'})
                        in_trade = None
                    elif c_high >= tp1:
                        in_trade['leg1_closed'] = True
                        if c_high >= tp2:
                            realized = 0.5 * 1.0 + 0.5 * tp2_mult
                            trades.append({'symbol': symbol, 'family': family, 'entry_time': in_trade['entry_time'],
                                           'exit_time': c_time, 'direction': direction, 'realized_r': realized,
                                           'outcome': 'TP1_AND_TP2'})
                            in_trade = None
                else:
                    if c_low <= be_price:
                        # 50% cerrado a 1R, 50% cerrado a BE (0R) = +0.50R neto
                        trades.append({'symbol': symbol, 'family': family, 'entry_time': in_trade['entry_time'],
                                       'exit_time': c_time, 'direction': direction, 'realized_r': 0.50,
                                       'outcome': 'TP1_THEN_BE'})
                        in_trade = None
                    elif c_high >= tp2:
                        realized = 0.5 * 1.0 + 0.5 * tp2_mult
                        trades.append({'symbol': symbol, 'family': family, 'entry_time': in_trade['entry_time'],
                                       'exit_time': c_time, 'direction': direction, 'realized_r': realized,
                                       'outcome': 'TP1_THEN_TP2'})
                        in_trade = None
            else: # SELL
                if not leg1_closed:
                    if c_high >= sl:
                        trades.append({'symbol': symbol, 'family': family, 'entry_time': in_trade['entry_time'],
                                       'exit_time': c_time, 'direction': direction, 'realized_r': -1.0,
                                       'outcome': 'SL_FULL'})
                        in_trade = None
                    elif c_low <= tp1:
                        in_trade['leg1_closed'] = True
                        if c_low <= tp2:
                            realized = 0.5 * 1.0 + 0.5 * tp2_mult
                            trades.append({'symbol': symbol, 'family': family, 'entry_time': in_trade['entry_time'],
                                           'exit_time': c_time, 'direction': direction, 'realized_r': realized,
                                           'outcome': 'TP1_AND_TP2'})
                            in_trade = None
                else:
                    if c_high >= be_price:
                        trades.append({'symbol': symbol, 'family': family, 'entry_time': in_trade['entry_time'],
                                       'exit_time': c_time, 'direction': direction, 'realized_r': 0.50,
                                       'outcome': 'TP1_THEN_BE'})
                        in_trade = None
                    elif c_low <= tp2:
                        realized = 0.5 * 1.0 + 0.5 * tp2_mult
                        trades.append({'symbol': symbol, 'family': family, 'entry_time': in_trade['entry_time'],
                                       'exit_time': c_time, 'direction': direction, 'realized_r': realized,
                                       'outcome': 'TP1_THEN_TP2'})
                        in_trade = None
            continue

        # 2. Gestionar Orden Pendiente (Limit Order Fill)
        if pending_order is not None:
            p = pending_order
            c_high = high[i]
            c_low = low[i]
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
                        tp1_price = actual_entry + risk_dist if p['direction'] == 'BUY' else actual_entry - risk_dist
                        tp2_price = actual_entry + risk_dist * tp2_mult if p['direction'] == 'BUY' else actual_entry - risk_dist * tp2_mult
                        be_price = actual_entry + (spread_points * 0.5 if p['direction'] == 'BUY' else -spread_points * 0.5)
                        
                        in_trade = {
                            'direction': p['direction'],
                            'entry': actual_entry,
                            'sl': p['sl'],
                            'tp1': tp1_price,
                            'tp2': tp2_price,
                            'be_price': be_price,
                            'leg1_closed': False,
                            'risk_dist': risk_dist,
                            'entry_time': df['time'].iloc[i],
                        }
                    pending_order = None
                    continue

        # 3. Detección de Setups SMC + Indicadores
        c_open = open_p[i]
        c_close = close[i]
        c_high = high[i]
        c_low = low[i]
        c_atr = atr14[i] if atr14[i] > 0 else 1.0
        c_adx = adx14[i] if not np.isnan(adx14[i]) else 0.0
        
        # Filtro de Régimen: ADX mínimo
        if c_adx < adx_threshold:
            continue
            
        local_swing_high = np.max(high[i - SWING_LOOKBACK:i])
        local_swing_low = np.min(low[i - SWING_LOOKBACK:i])
        
        # Track Liquidity Sweeps (en las últimas 4 barras)
        if c_high > local_swing_high:
            recent_sweep_high = {'bar': i, 'price': c_high}
        if c_low < local_swing_low:
            recent_sweep_low = {'bar': i, 'price': c_low}
            
        # Filtro de Tendencia HTF
        is_uptrend = c_close > ema_fast[i] and ema_fast[i] > ema_slow[i]
        is_downtrend = c_close < ema_fast[i] and ema_fast[i] < ema_slow[i]
        
        # --- REGLA CRASH: SOLO SELL (aprovechar caída/spikes y evitar muerte por compra) ---
        if family == 'CRASH':
            # Buscamos Setup de Venta:
            # 1. Hubo sweep de liquidez alcista reciente (en las últimas 6 barras)
            # 2. Desplazamiento bajista: vela bajista fuerte que crea FVG
            if recent_sweep_high and (i - recent_sweep_high['bar']) <= 6:
                # Condición FVG bajista: vela i-2 low > vela i high
                if low[i-2] > high[i] and (low[i-2] - high[i]) >= (0.15 * c_atr):
                    fvg_high = low[i-2]
                    fvg_low = high[i]
                    fvg_ce = (fvg_high + fvg_low) / 2.0
                    sl_level = recent_sweep_high['price'] + spread_points + (0.10 * c_atr)
                    pending_order = {
                        'direction': 'SELL',
                        'limit_price': fvg_ce,
                        'sl': sl_level,
                        'placed_bar': i,
                    }
                    recent_sweep_high = None

        # --- REGLA BOOM: SOLO BUY (aprovechar spikes alcistas y evitar muerte por venta) ---
        elif family == 'BOOM':
            # Setup de Compra:
            # 1. Hubo sweep de liquidez bajista reciente (últimas 6 barras)
            # 2. Desplazamiento alcista que crea FVG
            if recent_sweep_low and (i - recent_sweep_low['bar']) <= 6:
                if high[i-2] < low[i] and (low[i] - high[i-2]) >= (0.15 * c_atr):
                    fvg_low = high[i-2]
                    fvg_high = low[i]
                    fvg_ce = (fvg_high + fvg_low) / 2.0
                    sl_level = recent_sweep_low['price'] - spread_points - (0.10 * c_atr)
                    pending_order = {
                        'direction': 'BUY',
                        'limit_price': fvg_ce,
                        'sl': sl_level,
                        'placed_bar': i,
                    }
                    recent_sweep_low = None

        # --- REGLA STEP Y VOLATILITY: BIDIRECCIONAL SEGÚN TENDENCIA ---
        else: # STEP / VOLATILITY
            # VENTA: Tendencia bajista + sweep reciente de swing high + FVG bajista
            if is_downtrend and recent_sweep_high and (i - recent_sweep_high['bar']) <= 6:
                if low[i-2] > high[i] and (low[i-2] - high[i]) >= (0.20 * c_atr):
                    fvg_high = low[i-2]
                    fvg_low = high[i]
                    fvg_ce = (fvg_high + fvg_low) / 2.0
                    sl_level = recent_sweep_high['price'] + spread_points + (0.15 * c_atr)
                    pending_order = {
                        'direction': 'SELL',
                        'limit_price': fvg_ce,
                        'sl': sl_level,
                        'placed_bar': i,
                    }
                    recent_sweep_high = None

            # COMPRA: Tendencia alcista + sweep reciente de swing low + FVG alcista
            elif is_uptrend and recent_sweep_low and (i - recent_sweep_low['bar']) <= 6:
                if high[i-2] < low[i] and (low[i] - high[i-2]) >= (0.20 * c_atr):
                    fvg_low = high[i-2]
                    fvg_high = low[i]
                    fvg_ce = (fvg_high + fvg_low) / 2.0
                    sl_level = recent_sweep_low['price'] - spread_points - (0.15 * c_atr)
                    pending_order = {
                        'direction': 'BUY',
                        'limit_price': fvg_ce,
                        'sl': sl_level,
                        'placed_bar': i,
                    }
                    recent_sweep_low = None

    res_df = pd.DataFrame(trades)
    print(f"\n{'='*75}")
    print(f"REPLAY FIEL: QSS-4P (SMC + FVG + ADX) -> {symbol} [{family}]")
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

if __name__ == '__main__':
    run_scalper_backtest('data/historical/Crash_1000_Index_M5.csv', 'Crash 1000 Index', family='CRASH', spread_points=0.5, tp2_mult=2.5, adx_threshold=18.0)
    run_scalper_backtest('data/historical/Boom_1000_Index_M5.csv', 'Boom 1000 Index', family='BOOM', spread_points=1.0, tp2_mult=2.5, adx_threshold=18.0)
    run_scalper_backtest('data/historical/Step_Index_M5.csv', 'Step Index', family='STEP', spread_points=2.0, tp2_mult=2.0, adx_threshold=24.0)
    run_scalper_backtest('data/historical/Volatility_75_Index_M5.csv', 'Volatility 75 Index', family='VOLATILITY', spread_points=10.0, tp2_mult=2.5, adx_threshold=22.0)
    run_scalper_backtest('data/historical/Volatility_100_Index_M5.csv', 'Volatility 100 Index', family='VOLATILITY', spread_points=5.0, tp2_mult=2.5, adx_threshold=22.0)
