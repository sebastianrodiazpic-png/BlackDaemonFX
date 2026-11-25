import pandas as pd
import numpy as np

def run_scalping_replay(csv_path, symbol_name, spread_points=2.0, point_multiplier=1.0):
    df = pd.read_csv(csv_path)
    df['time'] = pd.to_datetime(df['time'])
    df = df.sort_values('time').reset_index(drop=True)
    
    n_candles = len(df)
    print(f"\n{'='*70}")
    print(f"REPLAY FIEL SCALPING M5: {symbol_name} ({n_candles} velas)")
    print(f"{'='*70}")
    
    # Pre-calcular ATR M5 de 14 periodos para filtros de volatilidad
    high = df['high'].values
    low = df['low'].values
    close = df['close'].values
    open_p = df['open'].values
    
    tr = np.maximum(high[1:] - low[1:], np.maximum(abs(high[1:] - close[:-1]), abs(low[1:] - close[:-1])))
    tr = np.insert(tr, 0, high[0] - low[0])
    atr14 = pd.Series(tr).rolling(14).mean().values
    
    # Pre-calcular EMA50 para sesgo tendencial HTF rápido en M5
    ema50 = pd.Series(close).ewm(span=50, adjust=False).mean().values
    
    trades = []
    in_trade = False
    pending_limit = None
    
    # Reglas del Scalper M5:
    # 1. Sweep de un swing local de 12 velas (High o Low)
    # 2. Vela de desplazamiento opuesta (cuerpo >= 50% del rango total de la vela y quiebra el cierre previo)
    # 3. Formación de FVG M5 (entre vela i-2 y vela i)
    # 4. Limit order en el 50% CE del FVG, activa por máximo 6 velas M5 (30 minutos)
    # 5. TP1 en 1.0R (pata 1), Pata 2 pasa a BE al tocar TP1 y busca TP2 en 2.0R
    
    SWING_WINDOW = 12
    MAX_PENDING_BARS = 6
    
    i = SWING_WINDOW + 3
    while i < n_candles - 1:
        # Si hay trade abierto, simular resolución bar por bar
        if in_trade:
            # Trade activo: resolver hasta SL, TP1, BE o TP2
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
            risk_dist = pos['risk_dist']
            
            # Chequeo conservador de conflicto intra-vela: SL siempre tiene prioridad si toca ambos
            if direction == 'BUY':
                if not leg1_closed:
                    # Ambas piernas en riesgo
                    if c_low <= sl:
                        # Stop Loss ejecutado para ambas piernas (-0.5R + -0.5R = -1.0R)
                        trades.append({
                            'symbol': symbol_name,
                            'entry_time': pos['entry_time'],
                            'exit_time': c_time,
                            'direction': direction,
                            'entry': entry,
                            'sl': sl,
                            'realized_r': -1.0,
                            'outcome': 'SL_FULL',
                            'leg1_r': -0.5,
                            'leg2_r': -0.5,
                        })
                        in_trade = False
                    elif c_high >= tp1:
                        # Pata 1 toca TP1 (+0.5R), Pata 2 pasa a Break Even
                        pos['leg1_closed'] = True
                        pos['leg1_r'] = 0.5  # 1.0R sobre pata de 0.5%
                        # Si en la misma vela toca TP2:
                        if c_high >= tp2:
                            trades.append({
                                'symbol': symbol_name,
                                'entry_time': pos['entry_time'],
                                'exit_time': c_time,
                                'direction': direction,
                                'entry': entry,
                                'sl': sl,
                                'realized_r': 1.5,  # 0.5R (leg1) + 1.0R (leg2 a 2R) = 1.5R total
                                'outcome': 'TP1_AND_TP2',
                                'leg1_r': 0.5,
                                'leg2_r': 1.0,
                            })
                            in_trade = False
                else:
                    # Pata 1 ya cerró. Pata 2 en Break Even protegida
                    if c_low <= be_price:
                        # Pata 2 cierra en BE (0.0R)
                        trades.append({
                            'symbol': symbol_name,
                            'entry_time': pos['entry_time'],
                            'exit_time': c_time,
                            'direction': direction,
                            'entry': entry,
                            'sl': sl,
                            'realized_r': 0.5,  # 0.5R de leg 1 + 0.0 de leg 2
                            'outcome': 'TP1_THEN_BE',
                            'leg1_r': 0.5,
                            'leg2_r': 0.0,
                        })
                        in_trade = False
                    elif c_high >= tp2:
                        # Pata 2 alcanza TP2 (+2.0R sobre 0.5% = +1.0R)
                        trades.append({
                            'symbol': symbol_name,
                            'entry_time': pos['entry_time'],
                            'exit_time': c_time,
                            'direction': direction,
                            'entry': entry,
                            'sl': sl,
                            'realized_r': 1.5,
                            'outcome': 'TP1_THEN_TP2',
                            'leg1_r': 0.5,
                            'leg2_r': 1.0,
                        })
                        in_trade = False
            else: # SELL
                if not leg1_closed:
                    if c_high >= sl:
                        trades.append({
                            'symbol': symbol_name,
                            'entry_time': pos['entry_time'],
                            'exit_time': c_time,
                            'direction': direction,
                            'entry': entry,
                            'sl': sl,
                            'realized_r': -1.0,
                            'outcome': 'SL_FULL',
                            'leg1_r': -0.5,
                            'leg2_r': -0.5,
                        })
                        in_trade = False
                    elif c_low <= tp1:
                        pos['leg1_closed'] = True
                        pos['leg1_r'] = 0.5
                        if c_low <= tp2:
                            trades.append({
                                'symbol': symbol_name,
                                'entry_time': pos['entry_time'],
                                'exit_time': c_time,
                                'direction': direction,
                                'entry': entry,
                                'sl': sl,
                                'realized_r': 1.5,
                                'outcome': 'TP1_AND_TP2',
                                'leg1_r': 0.5,
                                'leg2_r': 1.0,
                            })
                            in_trade = False
                else:
                    if c_high >= be_price:
                        trades.append({
                            'symbol': symbol_name,
                            'entry_time': pos['entry_time'],
                            'exit_time': c_time,
                            'direction': direction,
                            'entry': entry,
                            'sl': sl,
                            'realized_r': 0.5,
                            'outcome': 'TP1_THEN_BE',
                            'leg1_r': 0.5,
                            'leg2_r': 0.0,
                        })
                        in_trade = False
                    elif c_low <= tp2:
                        trades.append({
                            'symbol': symbol_name,
                            'entry_time': pos['entry_time'],
                            'exit_time': c_time,
                            'direction': direction,
                            'entry': entry,
                            'sl': sl,
                            'realized_r': 1.5,
                            'outcome': 'TP1_THEN_TP2',
                            'leg1_r': 0.5,
                            'leg2_r': 1.0,
                        })
                        in_trade = False
            i += 1
            continue

        # Si hay orden límite pendiente, comprobar si se ejecuta en esta vela
        if pending_limit:
            p = pending_limit
            c_high = high[i]
            c_low = low[i]
            
            # Verificar expiración de la orden límite
            if i - p['placed_bar'] > MAX_PENDING_BARS:
                pending_limit = None
            else:
                # Fill si el precio cruza el nivel límite
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
                            'direction': p['direction'],
                            'entry': actual_entry,
                            'sl': p['sl'],
                            'tp1': actual_entry + risk_dist * 1.0 if p['direction'] == 'BUY' else actual_entry - risk_dist * 1.0,
                            'tp2': actual_entry + risk_dist * 2.0 if p['direction'] == 'BUY' else actual_entry - risk_dist * 2.0,
                            'be_price': actual_entry + (spread_points if p['direction'] == 'BUY' else -spread_points),
                            'leg1_closed': False,
                            'leg1_r': 0.0,
                            'risk_dist': risk_dist,
                            'entry_time': df['time'].iloc[i],
                        }
                    pending_limit = None
                    i += 1
                    continue

        # Evaluar formación de setup al cierre de la vela i (sin lookahead)
        # 1. Sweep del swing de los últimos SWING_WINDOW bares
        local_swing_high = np.max(high[i - SWING_WINDOW:i])
        local_swing_low = np.min(low[i - SWING_WINDOW:i])
        
        c_open = open_p[i]
        c_close = close[i]
        c_high = high[i]
        c_low = low[i]
        bar_range = c_high - c_low
        body = abs(c_close - c_open)
        
        # Filtro de calidad de vela: cuerpo representativo
        if bar_range > 0 and (body / bar_range) >= 0.50:
            # Caso BEARISH: Sweep de swing high seguido de vela bajista fuerte con quiebre de estructura
            if high[i-1] >= local_swing_high or c_high >= local_swing_high:
                if c_close < c_open and c_close < low[i-1]:  # Vela bajista desplaza bajo el mínimo previo
                    # FVG entre low[i-2] y high[i]
                    if low[i-2] > c_high:
                        fvg_top = low[i-2]
                        fvg_bot = c_high
                        fvg_ce = (fvg_top + fvg_bot) / 2.0
                        sl_price = max(c_high, high[i-1]) + spread_points
                        
                        # Sesgo: precio bajo EMA50 o dentro de retroceso
                        pending_limit = {
                            'direction': 'SELL',
                            'limit_price': fvg_ce,
                            'sl': sl_price,
                            'placed_bar': i,
                            'signal_time': df['time'].iloc[i],
                        }
            
            # Caso BULLISH: Sweep de swing low seguido de vela alcista fuerte con quiebre de estructura
            elif low[i-1] <= local_swing_low or c_low <= local_swing_low:
                if c_close > c_open and c_close > high[i-1]:  # Vela alcista desplaza sobre el máximo previo
                    # FVG entre high[i-2] y low[i]
                    if high[i-2] < c_low:
                        fvg_bot = high[i-2]
                        fvg_top = c_low
                        fvg_ce = (fvg_top + fvg_bot) / 2.0
                        sl_price = min(c_low, low[i-1]) - spread_points
                        
                        pending_limit = {
                            'direction': 'BUY',
                            'limit_price': fvg_ce,
                            'sl': sl_price,
                            'placed_bar': i,
                            'signal_time': df['time'].iloc[i],
                        }
        
        i += 1

    # Reporte de resultados
    res_df = pd.DataFrame(trades)
    if len(res_df) == 0:
        print("No se generaron trades con estos criterios.")
        return None
        
    print(f"Total trades completados: {len(res_df)}")
    wins = res_df[res_df['realized_r'] > 0]
    losses = res_df[res_df['realized_r'] < 0]
    be = res_df[res_df['realized_r'] == 0]
    
    wr = len(wins) / len(res_df) * 100
    total_r = res_df['realized_r'].sum()
    avg_r = res_df['realized_r'].mean()
    gross_win = wins['realized_r'].sum()
    gross_loss = abs(losses['realized_r'].sum())
    pf = (gross_win / gross_loss) if gross_loss > 0 else np.inf
    
    print(f"Win Rate Global: {wr:.2f}% (Wins: {len(wins)}, Losses: {len(losses)})")
    print(f"R Neto Acumulado: {total_r:+.2f} R | R/trade: {avg_r:+.3f} R | Profit Factor: {pf:.2f}")
    print(f"Distribución de resultados:")
    print(res_df['outcome'].value_counts().to_string())
    
    # Validación estricta por dos mitades (Criterio obligatorio Regla 3)
    half = len(res_df) // 2
    part1 = res_df.iloc[:half]
    part2 = res_df.iloc[half:]
    
    r1 = part1['realized_r'].sum()
    wr1 = (part1['realized_r'] > 0).mean() * 100
    r2 = part2['realized_r'].sum()
    wr2 = (part2['realized_r'] > 0).mean() * 100
    
    print("\n--- VALIDACIÓN EN AMBAS MITADES (Regla 3 del Proyecto) ---")
    print(f"Mitad 1 ({len(part1)} ops, {part1['entry_time'].iloc[0]} a {part1['entry_time'].iloc[-1]}): {r1:+.2f} R (WR: {wr1:.1f}%)")
    print(f"Mitad 2 ({len(part2)} ops, {part2['entry_time'].iloc[0]} a {part2['entry_time'].iloc[-1]}): {r2:+.2f} R (WR: {wr2:.1f}%)")
    
    valido = r1 > 0 and r2 > 0 and len(part1) >= 40 and len(part2) >= 40
    print(f"Resultado de Validación: {'APROBADO CON ÉXITO' if valido else 'NO CUMPLE CRITERIO'}")
    return res_df

# Run across the 4 key assets
for sym, path, sp in [
    ('Step Index', 'data/historical/Step_Index_M5.csv', 2.0),
    ('Crash 1000 Index', 'data/historical/Crash_1000_Index_M5.csv', 0.5),
    ('Boom 1000 Index', 'data/historical/Boom_1000_Index_M5.csv', 1.0),
    ('Volatility 75 Index', 'data/historical/Volatility_75_Index_M5.csv', 10.0),
]:
    run_scalping_replay(path, sym, spread_points=sp)
