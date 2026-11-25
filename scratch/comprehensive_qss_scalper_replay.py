import pandas as pd
import numpy as np
import math

def calculate_adx_and_ci(df, period=14):
    high = df['high'].values
    low = df['low'].values
    close = df['close'].values
    n = len(df)
    
    # True Range
    tr = np.maximum(high[1:] - low[1:], np.maximum(abs(high[1:] - close[:-1]), abs(low[1:] - close[:-1])))
    tr = np.insert(tr, 0, high[0] - low[0])
    
    # DM+ y DM-
    up_move = high[1:] - high[:-1]
    down_move = low[:-1] - low[1:]
    plus_dm = np.where((up_move > down_move) & (up_move > 0), up_move, 0.0)
    minus_dm = np.where((down_move > up_move) & (down_move > 0), down_move, 0.0)
    plus_dm = np.insert(plus_dm, 0, 0.0)
    minus_dm = np.insert(minus_dm, 0, 0.0)
    
    # Rolling ATR & DMs
    tr_series = pd.Series(tr)
    atr = tr_series.rolling(period).mean().values
    plus_di = 100.0 * pd.Series(plus_dm).rolling(period).mean().values / np.where(atr > 0, atr, 1.0)
    minus_di = 100.0 * pd.Series(minus_dm).rolling(period).mean().values / np.where(atr > 0, atr, 1.0)
    
    # DX y ADX
    sum_di = plus_di + minus_di
    dx = 100.0 * np.abs(plus_di - minus_di) / np.where(sum_di > 0, sum_di, 1.0)
    adx = pd.Series(dx).rolling(period).mean().values
    
    # Choppiness Index
    # CI = 100 * LOG10( SUM(TR, 14) / (MaxHigh14 - MinLow14) ) / LOG10(14)
    sum_tr = tr_series.rolling(period).sum().values
    max_h = pd.Series(high).rolling(period).max().values
    min_l = pd.Series(low).rolling(period).min().values
    hl_range = max_h - min_l
    
    ratio = np.where(hl_range > 0, sum_tr / hl_range, 1.0)
    ratio = np.where(ratio > 0, ratio, 1.0)
    ci = 100.0 * np.log10(ratio) / np.log10(period)
    
    return atr, adx, ci

def run_scalper_replay_symbol(m5_path, h1_path, symbol_name, family, spread_points, tp2_rr=2.0):
    df_m5 = pd.read_csv(m5_path)
    df_m5['time'] = pd.to_datetime(df_m5['time'])
    df_m5 = df_m5.sort_values('time').reset_index(drop=True)
    
    df_h1 = pd.read_csv(h1_path)
    df_h1['time'] = pd.to_datetime(df_h1['time'])
    df_h1 = df_h1.sort_values('time').reset_index(drop=True)
    
    # H1 Trend Context
    df_h1['ema50'] = df_h1['close'].ewm(span=50, adjust=False).mean()
    df_h1['ema200'] = df_h1['close'].ewm(span=200, adjust=False).mean()
    df_h1['h1_close_time'] = df_h1['time'] + pd.Timedelta(hours=1)
    
    # Merge H1 cerrado a M5 (cero lookahead)
    m5 = pd.merge_asof(
        df_m5,
        df_h1[['h1_close_time', 'ema50', 'ema200']],
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
    
    atr14, adx14, ci14 = calculate_adx_and_ci(m5, period=14)
    
    # Thresholds por familia
    min_adx = 28.0 if family == 'STEP' else (22.0 if family == 'VOLATILITY' else 18.0)
    max_ci = 50.0 # Bloquea consolidaciones erráticas
    
    trades = []
    in_trade = None
    pending_order = None
    
    SWING_WINDOW = 20
    MAX_PENDING_BARS = 6
    
    # Registro de sweep reciente
    recent_sweep = None
    
    # Warmup
    start_bar = 250
    for i in range(start_bar, n):
        c_time = times[i]
        c_high = high[i]
        c_low = low[i]
        c_close = close[i]
        c_open = open_p[i]
        c_atr = atr14[i] if (not np.isnan(atr14[i]) and atr14[i] > 0) else 1.0
        c_adx = adx14[i] if not np.isnan(adx14[i]) else 0.0
        c_ci = ci14[i] if not np.isnan(ci14[i]) else 60.0
        
        # 1. Gestionar trade en curso
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
            
        # 2. Gestionar orden limit pendiente
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

        # 3. Filtros Cuantitativos de Régimen
        if c_adx < min_adx or c_ci > max_ci:
            continue
            
        h1_ema50 = m5['ema50'].iloc[i]
        h1_ema200 = m5['ema200'].iloc[i]
        if pd.isna(h1_ema50):
            continue
            
        # Swing High y Swing Low locales M5
        local_swing_h = np.max(high[i - SWING_WINDOW:i])
        local_swing_l = np.min(low[i - SWING_WINDOW:i])
        
        # Detectar Sweep
        bar_range = c_high - c_low
        if bar_range > 0:
            upper_wick = c_high - max(c_open, c_close)
            lower_wick = min(c_open, c_close) - c_low
            
            # Sweep alcista (candidato para SELL)
            if c_high > local_swing_h and (upper_wick / bar_range) >= 0.25:
                recent_sweep = {'type': 'BEARISH_SWEEP', 'bar': i, 'peak': c_high}
            # Sweep bajista (candidato para BUY)
            elif c_low < local_swing_l and (lower_wick / bar_range) >= 0.25:
                recent_sweep = {'type': 'BULLISH_SWEEP', 'bar': i, 'trough': c_low}
                
        # Buscar Gatillo MSS + FVG si hubo sweep en las últimas 5 barras
        if recent_sweep is not None:
            bars_since = i - recent_sweep['bar']
            if bars_since > 5:
                recent_sweep = None
            else:
                # Caso Venta: Crash, Step, Volatility
                can_sell = (family in ['CRASH', 'STEP', 'VOLATILITY'])
                h1_bearish = (family == 'CRASH') or (c_close < h1_ema50)
                
                if can_sell and h1_bearish and recent_sweep['type'] == 'BEARISH_SWEEP':
                    # MSS: Desplazamiento bajista cerrando por debajo del mínimo de la vela previa
                    if c_close < low[i-1]:
                        # FVG bajista entre i-2 y vela actual
                        if low[i-2] > c_high and (low[i-2] - c_high) >= (0.10 * c_atr):
                            fvg_ce = (low[i-2] + c_high) / 2.0
                            sl_level = recent_sweep['peak'] + spread_points + (0.15 * c_atr)
                            pending_order = {
                                'direction': 'SELL', 'limit_price': fvg_ce, 'sl': sl_level,
                                'placed_bar': i
                            }
                            recent_sweep = None
                            
                # Caso Compra: Boom, Step, Volatility
                can_buy = (family in ['BOOM', 'STEP', 'VOLATILITY'])
                h1_bullish = (family == 'BOOM') or (c_close > h1_ema50)
                
                if can_buy and h1_bullish and recent_sweep and recent_sweep['type'] == 'BULLISH_SWEEP':
                    if c_close > high[i-1]:
                        # FVG alcista entre i-2 y vela actual
                        if high[i-2] < c_low and (c_low - high[i-2]) >= (0.10 * c_atr):
                            fvg_ce = (high[i-2] + c_low) / 2.0
                            sl_level = recent_sweep['trough'] - spread_points - (0.15 * c_atr)
                            pending_order = {
                                'direction': 'BUY', 'limit_price': fvg_ce, 'sl': sl_level,
                                'placed_bar': i
                            }
                            recent_sweep = None

    # Métricas y Análisis
    res_df = pd.DataFrame(trades)
    if len(res_df) == 0:
        return {'symbol': symbol_name, 'family': family, 'trades': 0, 'wr': 0, 'total_r': 0, 'mdd_r': 0, 'pf': 0}
        
    wins = res_df[res_df['realized_r'] > 0]
    losses = res_df[res_df['realized_r'] < 0]
    wr = len(wins) / len(res_df) * 100.0
    total_r = res_df['realized_r'].sum()
    gross_win = wins['realized_r'].sum()
    gross_loss = abs(losses['realized_r'].sum())
    pf = (gross_win / gross_loss) if gross_loss > 0 else np.inf
    
    # Curva de equidad y Max Drawdown en R
    equity_curve = res_df['realized_r'].cumsum()
    running_max = np.maximum.accumulate(equity_curve)
    drawdowns = running_max - equity_curve
    max_dd_r = np.max(drawdowns)
    
    # Asumiendo 1% de riesgo por R sobre cuenta inicial de $10,000 USD
    initial_balance = 10000.0
    balance = initial_balance
    peak_bal = initial_balance
    max_dd_pct = 0.0
    for r in res_df['realized_r']:
        risk_usd = balance * 0.01
        pnl = r * risk_usd
        balance += pnl
        if balance > peak_bal:
            peak_bal = balance
        dd_pct = (peak_bal - balance) / peak_bal * 100.0
        if dd_pct > max_dd_pct:
            max_dd_pct = dd_pct
    total_gain_usd = balance - initial_balance
    total_gain_pct = (total_gain_usd / initial_balance) * 100.0
    
    return {
        'symbol': symbol_name,
        'family': family,
        'trades': len(res_df),
        'wr': wr,
        'total_r': total_r,
        'pf': pf,
        'max_dd_r': max_dd_r,
        'max_dd_pct': max_dd_pct,
        'final_balance': balance,
        'gain_usd': total_gain_usd,
        'gain_pct': total_gain_pct,
        'outcomes': res_df['outcome'].value_counts().to_dict(),
        'res_df': res_df
    }

if __name__ == '__main__':
    targets = [
        ('data/historical/Crash_1000_Index_M5.csv', 'data/historical/Crash_1000_Index_H1.csv', 'Crash 1000 Index', 'CRASH', 0.5),
        ('data/historical/Boom_1000_Index_M5.csv', 'data/historical/Boom_1000_Index_H1.csv', 'Boom 1000 Index', 'BOOM', 1.0),
        ('data/historical/Step_Index_M5.csv', 'data/historical/Step_Index_H1.csv', 'Step Index', 'STEP', 2.0),
        ('data/historical/Volatility_75_Index_M5.csv', 'data/historical/Volatility_75_Index_H1.csv', 'Volatility 75 Index', 'VOLATILITY', 10.0),
        ('data/historical/Volatility_100_Index_M5.csv', 'data/historical/Volatility_100_Index_H1.csv', 'Volatility 100 Index', 'VOLATILITY', 5.0),
    ]
    
    print("=" * 80)
    print("INICIANDO REPLAY MULTIANUAL QSS-4P (ANCLAJE H1 + RÉGIMEN ADX/CI + M5 FVG + 1% SPLIT)")
    print("=" * 80)
    
    summary = []
    for m5_p, h1_p, sym, fam, sp in targets:
        print(f"Ejecutando {sym} [{fam}]...")
        res = run_scalper_replay_symbol(m5_p, h1_p, sym, fam, spread_points=sp, tp2_rr=2.0)
        summary.append(res)
        print(f"-> {sym}: {res['trades']} trades | WR: {res['wr']:.1f}% | R Neto: {res['total_r']:+.2f} R | PF: {res['pf']:.2f} | MaxDD: {res['max_dd_pct']:.2f}% | Ganancia: ${res.get('gain_usd', 0):+.2f} ({res.get('gain_pct', 0):+.1f}%)")
        if 'outcomes' in res:
            print(f"   Detalle: {res['outcomes']}")
        print("-" * 80)
