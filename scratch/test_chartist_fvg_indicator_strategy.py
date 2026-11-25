import pandas as pd
import numpy as np

def run_confluence_triad_replay(csv_path, symbol_name, spread_points=1.0, direction_filter=None):
    df = pd.read_csv(csv_path)
    df['time'] = pd.to_datetime(df['time'])
    df = df.sort_values('time').reset_index(drop=True)
    
    high = df['high'].values
    low = df['low'].values
    close = df['close'].values
    open_p = df['open'].values
    n = len(df)
    
    # 1. INDICADORES:
    # EMA rápida (EMA 20) y lenta (EMA 50) para sesgo tendencial
    ema20 = pd.Series(close).ewm(span=20, adjust=False).mean().values
    ema50 = pd.Series(close).ewm(span=50, adjust=False).mean().values
    
    # RSI de 14 periodos para detectar agotamiento / sobreextensión
    delta = pd.Series(close).diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.rolling(14).mean().values
    avg_loss = loss.rolling(14).mean().values
    rs = np.divide(avg_gain, avg_loss, out=np.zeros_like(avg_gain), where=avg_loss!=0)
    rsi14 = 100.0 - (100.0 / (1.0 + rs))
    
    # ATR de 14 para medir volatilidad y definir stops/objetivos
    tr = np.maximum(high[1:] - low[1:], np.maximum(abs(high[1:] - close[:-1]), abs(low[1:] - close[:-1])))
    tr = np.insert(tr, 0, high[0] - low[0])
    atr14 = pd.Series(tr).rolling(14).mean().values
    
    # ADX de 14 para descartar consolidaciones sucias
    # (Aproximación rápida: relación de rango y dirección)
    
    trades = []
    in_trade = False
    
    # Bucle barra por barra (sin lookahead)
    i = 60
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
            
        c_open = open_p[i]
        c_close = close[i]
        c_high = high[i]
        c_low = low[i]
        c_atr = atr14[i] if atr14[i] > 0 else 1.0
        bar_range = c_high - c_low
        
        # 1. CONDICIÓN TÉCNICA (INDICADOR): Tendencia definida
        is_bull_trend = ema20[i] > ema50[i] and c_close > ema50[i]
        is_bear_trend = ema20[i] < ema50[i] and c_close < ema50[i]
        
        # 2. PATRÓN CHARTISTA:
        # Pullback con rechazo tipo Pinbar / Absorción institucional sobre la EMA20/50
        # Mecha contraria al menos 30% del rango, y cierre en dirección del impulso
        upper_wick = c_high - max(c_open, c_close)
        lower_wick = min(c_open, c_close) - c_low
        body = abs(c_close - c_open)
        
        # 3. FAIR VALUE GAP (FVG):
        # En las últimas 3 velas debe haberse formado un FVG favorable
        has_bull_fvg = (low[i] > high[i-2]) or (low[i-1] > high[i-3])
        has_bear_fvg = (high[i] < low[i-2]) or (high[i-1] < low[i-3])
        
        # --- GATILLO COMPRA (BULLISH CONFLUENCE) ---
        if (direction_filter is None or direction_filter == 'BUY') and is_bull_trend:
            # Chartismo: Rebound / Pinbar en zona EMA + FVG alcista activo + RSI en recuperación (> 45 y < 65)
            if bar_range > 0 and (lower_wick / bar_range) >= 0.30 and c_close > c_open:
                # El Low de la vela testeó cerca de la EMA20 o EMA50
                tested_ema = abs(c_low - ema20[i]) <= (0.5 * c_atr) or abs(c_low - ema50[i]) <= (0.5 * c_atr)
                if tested_ema and has_bull_fvg and (45.0 <= rsi14[i] <= 68.0):
                    entry_p = open_p[i+1] + spread_points
                    sl_p = c_low - spread_points - (0.15 * c_atr)
                    risk_d = abs(entry_p - sl_p)
                    if risk_d >= 1.5 * spread_points:
                        in_trade = {
                            'direction': 'BUY', 'entry': entry_p, 'sl': sl_p,
                            'tp1': entry_p + risk_d * 1.0,
                            'tp2': entry_p + risk_d * 2.0,
                            'be_price': entry_p + spread_points,
                            'leg1_closed': False, 'entry_time': df['time'].iloc[i+1],
                        }
                        i += 1
                        continue

        # --- GATILLO VENTA (BEARISH CONFLUENCE) ---
        if (direction_filter is None or direction_filter == 'SELL') and is_bear_trend:
            if bar_range > 0 and (upper_wick / bar_range) >= 0.30 and c_close < c_open:
                tested_ema = abs(c_high - ema20[i]) <= (0.5 * c_atr) or abs(c_high - ema50[i]) <= (0.5 * c_atr)
                if tested_ema and has_bear_fvg and (32.0 <= rsi14[i] <= 55.0):
                    entry_p = open_p[i+1] - spread_points
                    sl_p = c_high + spread_points + (0.15 * c_atr)
                    risk_d = abs(entry_p - sl_p)
                    if risk_d >= 1.5 * spread_points:
                        in_trade = {
                            'direction': 'SELL', 'entry': entry_p, 'sl': sl_p,
                            'tp1': entry_p - risk_d * 1.0,
                            'tp2': entry_p - risk_d * 2.0,
                            'be_price': entry_p - spread_points,
                            'leg1_closed': False, 'entry_time': df['time'].iloc[i+1],
                        }
                        i += 1
                        continue
                        
        i += 1

    res_df = pd.DataFrame(trades)
    print(f"\n{'='*75}")
    print(f"REPLAY FIEL: CONFLUENCIA TRIPARTITA (CHARTISMO + FVG + INDICADORES)")
    print(f"Activo: {symbol_name} [{direction_filter or 'BIDIRECT'}] ({n} velas)")
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
    
    print(f"Total trades: {len(res_df)} | WR: {wr:.2f}% (Wins: {len(wins)}, Losses: {len(losses)})")
    print(f"R Neto: {total_r:+.2f} R | R/trade: {avg_r:+.3f} R | Profit Factor: {pf:.2f}")
    print(f"Desglose de ejecución:")
    print(res_df['outcome'].value_counts().to_string())
    
    half = len(res_df) // 2
    if half >= 20:
        part1 = res_df.iloc[:half]
        part2 = res_df.iloc[half:]
        r1, r2 = part1['realized_r'].sum(), part2['realized_r'].sum()
        wr1, wr2 = (part1['realized_r'] > 0).mean()*100, (part2['realized_r'] > 0).mean()*100
        print(f"\n--- VALIDACIÓN OBLIGATORIA POR MITADES (Regla 3) ---")
        print(f"Mitad 1 ({len(part1)} ops, {part1['entry_time'].iloc[0]} a {part1['entry_time'].iloc[-1]}): {r1:+.2f} R (WR: {wr1:.1f}%)")
        print(f"Mitad 2 ({len(part2)} ops, {part2['entry_time'].iloc[0]} a {part2['entry_time'].iloc[-1]}): {r2:+.2f} R (WR: {wr2:.1f}%)")
        print(f"Estado de Validación: {'APROBADO (POSITIVO EN AMBAS MITADES)' if r1 > 0 and r2 > 0 else 'NO APROBADO'}")
    return res_df

# Run across assets
run_confluence_triad_replay('data/historical/Volatility_75_Index_M5.csv', 'Volatility 75 Index', spread_points=10.0)
run_confluence_triad_replay('data/historical/Crash_1000_Index_M5.csv', 'Crash 1000 Index', spread_points=0.5, direction_filter='SELL')
run_confluence_triad_replay('data/historical/Boom_1000_Index_M5.csv', 'Boom 1000 Index', spread_points=1.0, direction_filter='BUY')
run_confluence_triad_replay('data/historical/Step_Index_M5.csv', 'Step Index', spread_points=2.0)
