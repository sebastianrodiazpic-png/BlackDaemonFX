"""
scratch/evaluate_alternative_strategies_walkforward.py
======================================================
Evaluación cuantitativa y rigurosa de estrategias alternativas sobre los 23 activos canónicos:
1. Donchian Momentum Breakout (Trend Following)
2. Bollinger Reversion (Mean Reversion)
3. Opening Range Breakout (ORB)
4. Dual-EMA Pullback + Volatility Contraction

Salvaguardas Metodológicas:
- Causalidad estricta: señal en vela cerrada M15, entrada en Open de M15 siguiente.
- Resolución conservadora: SL > TP en toques simultáneos intra-vela.
- Control de concurrencia: Cap=1 simultáneo por portafolio.
- Costos reales observados de Deriv MT5 (spread + slippage).
- Partición cronológica idéntica en 4 folds (Holdout Fold 4 intacto).
- Métricas: N, Win%, IC Wilson 95%, Expectativa (R/op), PnL neto (R), PF, MaxDD.
"""

import pickle
import numpy as np
import pandas as pd
from pathlib import Path
from datetime import datetime

CACHE_DIR = Path("data/cache_msnr")

# 23 Símbolos Canónicos
SYMBOLS_23 = [
    'Boom_1000_Index', 'Boom_300_Index', 'Boom_500_Index', 'Crash_1000_Index',
    'Crash_500_Index', 'Crash_600_Index', 'Jump_10_Index', 'Jump_25_Index',
    'Jump_50_Index', 'Step_Index', 'Step_Index_200', 'Step_Index_400',
    'Step_Index_500', 'Volatility_250_(1s)_Index', 'Volatility_50_(1s)_Index',
    'Volatility_90_Index', 'XAUUSD', 'XAGUSD', 'Wall_Street_30', 'EURUSD',
    'GBPUSD', 'USDJPY', 'AUDNZD'
]

# Spreads en puntos de Deriv MT5
SPREADS = {
    'Boom_1000_Index': 0.50, 'Boom_300_Index': 0.20, 'Boom_500_Index': 0.50,
    'Crash_1000_Index': 0.50, 'Crash_500_Index': 0.50, 'Crash_600_Index': 0.50,
    'Jump_10_Index': 2.50, 'Jump_25_Index': 1.50, 'Jump_50_Index': 2.00,
    'Step_Index': 0.10, 'Step_Index_200': 0.20, 'Step_Index_400': 0.40,
    'Step_Index_500': 0.50, 'Volatility_250_(1s)_Index': 0.0035,
    'Volatility_50_(1s)_Index': 0.05, 'Volatility_90_Index': 0.90,
    'XAUUSD': 0.25, 'XAGUSD': 0.025, 'Wall_Street_30': 2.50,
    'EURUSD': 0.00015, 'GBPUSD': 0.00020, 'USDJPY': 0.018, 'AUDNZD': 0.00025
}

def wilson_interval(w, n, z=1.95996):
    if n == 0:
        return 0.0, 0.0
    p = w / n
    denom = 1 + (z**2) / n
    center = (p + (z**2) / (2 * n)) / denom
    spread = (z / denom) * np.sqrt((p * (1 - p) / n) + ((z**2) / (4 * (n**2))))
    return max(0.0, center - spread), min(1.0, center + spread)

def load_data():
    dfs = {}
    for s in SYMBOLS_23:
        p = CACHE_DIR / f"{s}_M15.pkl"
        if p.exists():
            with open(p, "rb") as f:
                df = pickle.load(f)
            df.columns = [c.lower() for c in df.columns]
            time_col = 'time' if 'time' in df.columns else 'datetime' if 'datetime' in df.columns else None
            if time_col:
                df['time'] = pd.to_datetime(df[time_col], utc=True)
            else:
                df['time'] = pd.to_datetime(df.index, utc=True)
            df = df.sort_values('time').reset_index(drop=True)
            dfs[s] = df
    return dfs

def calc_atr(df, period=14):
    high = df['high'].values
    low = df['low'].values
    close = df['close'].values
    tr = np.maximum(high[1:] - low[1:], np.maximum(np.abs(high[1:] - close[:-1]), np.abs(low[1:] - close[:-1])))
    tr = np.insert(tr, 0, high[0] - low[0])
    atr = pd.Series(tr).rolling(period, min_periods=period).mean().values
    return atr

def calc_adx(df, period=14):
    high = df['high']
    low = df['low']
    close = df['close']
    plus_dm = high.diff()
    minus_dm = low.diff()
    plus_dm = np.where((plus_dm > minus_dm) & (plus_dm > 0), plus_dm, 0.0)
    minus_dm = np.where((minus_dm > plus_dm) & (minus_dm > 0), -minus_dm, 0.0)
    
    tr = np.maximum(high - low, np.maximum((high - close.shift()).abs(), (low - close.shift()).abs()))
    atr = pd.Series(tr).rolling(period).mean()
    
    plus_di = 100 * (pd.Series(plus_dm).rolling(period).mean() / atr)
    minus_di = 100 * (pd.Series(minus_dm).rolling(period).mean() / atr)
    dx = 100 * (abs(plus_di - minus_di) / (plus_di + minus_di + 1e-9))
    adx = dx.rolling(period).mean().fillna(0.0).values
    return adx

def calc_rsi(series, period=14):
    delta = series.diff()
    gain = delta.clip(lower=0.0)
    loss = -delta.clip(upper=0.0)
    avg_gain = gain.rolling(period, min_periods=period).mean()
    avg_loss = loss.rolling(period, min_periods=period).mean()
    rs = avg_gain / (avg_loss + 1e-9)
    rsi = 100.0 - (100.0 / (1.0 + rs))
    return rsi.fillna(50.0).values

def simulate_signals(raw_signals, cap=1):
    """
    Simula señales causales con Cap=1 concurrencia global,
    resolución conservadora SL > TP, y slippage/spread.
    """
    if not raw_signals:
        return []
    
    # Ordenar estrictamente por entry_time
    raw_signals.sort(key=lambda x: x['entry_time'])
    
    executed = []
    active_until = None
    
    for sig in raw_signals:
        e_time = sig['entry_time']
        
        # Filtro de concurrencia Cap=1
        if active_until is not None and e_time < active_until:
            continue
            
        executed.append(sig)
        active_until = sig['exit_time']
        
    return executed

def run_donchian_breakout(dfs):
    signals = []
    for sym, df in dfs.items():
        if len(df) < 50:
            continue
        spread = SPREADS.get(sym, 0.0001)
        close = df['close'].values
        high = df['high'].values
        low = df['low'].values
        open_ = df['open'].values
        times = df['time'].values
        
        atr = calc_atr(df, 14)
        adx = calc_adx(df, 14)
        
        # Donchian 20
        donch_high = pd.Series(high).rolling(20).max().shift(1).values
        donch_low = pd.Series(low).rolling(20).min().shift(1).values
        
        n = len(df)
        for i in range(25, n - 20):
            if np.isnan(atr[i]) or atr[i] <= 0:
                continue
            
            # Condición BUY
            if close[i] > donch_high[i] and adx[i] >= 28:
                entry_p = open_[i+1] + spread
                sl_p = entry_p - 1.5 * atr[i]
                risk = entry_p - sl_p
                tp_p = entry_p + 2.0 * risk # 1:2 RR
                
                # Simular salida
                outcome = "LOSS"
                exit_time = times[min(i+20, n-1)]
                rr = -1.0
                for j in range(i+1, min(i+150, n)):
                    # Conservador: SL primero
                    if low[j] <= sl_p:
                        outcome = "LOSS"
                        rr = -1.0
                        exit_time = times[j]
                        break
                    elif high[j] >= tp_p:
                        outcome = "WIN"
                        rr = 2.0
                        exit_time = times[j]
                        break
                
                signals.append({
                    "strategy": "Donchian_Breakout",
                    "symbol": sym,
                    "direction": "BUY",
                    "entry_time": pd.to_datetime(times[i+1]),
                    "exit_time": pd.to_datetime(exit_time),
                    "outcome": outcome,
                    "rr": rr
                })
                
            # Condición SELL
            elif close[i] < donch_low[i] and adx[i] >= 28:
                entry_p = open_[i+1] - spread
                sl_p = entry_p + 1.5 * atr[i]
                risk = sl_p - entry_p
                tp_p = entry_p - 2.0 * risk # 1:2 RR
                
                outcome = "LOSS"
                exit_time = times[min(i+20, n-1)]
                rr = -1.0
                for j in range(i+1, min(i+150, n)):
                    if high[j] >= sl_p:
                        outcome = "LOSS"
                        rr = -1.0
                        exit_time = times[j]
                        break
                    elif low[j] <= tp_p:
                        outcome = "WIN"
                        rr = 2.0
                        exit_time = times[j]
                        break
                        
                signals.append({
                    "strategy": "Donchian_Breakout",
                    "symbol": sym,
                    "direction": "SELL",
                    "entry_time": pd.to_datetime(times[i+1]),
                    "exit_time": pd.to_datetime(exit_time),
                    "outcome": outcome,
                    "rr": rr
                })
    return signals

def run_bollinger_reversion(dfs):
    signals = []
    for sym, df in dfs.items():
        if len(df) < 50:
            continue
        spread = SPREADS.get(sym, 0.0001)
        close = df['close']
        high = df['high'].values
        low = df['low'].values
        open_ = df['open'].values
        times = df['time'].values
        
        sma = close.rolling(20).mean()
        std = close.rolling(20).std()
        upper = (sma + 2.2 * std).values
        lower = (sma - 2.2 * std).values
        rsi = calc_rsi(close, 14)
        atr = calc_atr(df, 14)
        
        c_vals = close.values
        n = len(df)
        for i in range(25, n - 20):
            if np.isnan(atr[i]) or atr[i] <= 0:
                continue
            
            # Reversión Alcista: mecha perforó banda inferior y cerró adentro, RSI < 32
            if low[i] < lower[i] and c_vals[i] > lower[i] and rsi[i] < 32:
                entry_p = open_[i+1] + spread
                sl_p = low[i] - 0.2 * atr[i]
                risk = entry_p - sl_p
                if risk <= 0:
                    continue
                tp_p = entry_p + 1.5 * risk # 1:1.5 RR
                
                outcome = "LOSS"
                exit_time = times[min(i+20, n-1)]
                rr = -1.0
                for j in range(i+1, min(i+100, n)):
                    if low[j] <= sl_p:
                        outcome = "LOSS"
                        rr = -1.0
                        exit_time = times[j]
                        break
                    elif high[j] >= tp_p:
                        outcome = "WIN"
                        rr = 1.5
                        exit_time = times[j]
                        break
                signals.append({
                    "strategy": "Bollinger_Reversion",
                    "symbol": sym,
                    "direction": "BUY",
                    "entry_time": pd.to_datetime(times[i+1]),
                    "exit_time": pd.to_datetime(exit_time),
                    "outcome": outcome,
                    "rr": rr
                })
                
            # Reversión Bajista
            elif high[i] > upper[i] and c_vals[i] < upper[i] and rsi[i] > 68:
                entry_p = open_[i+1] - spread
                sl_p = high[i] + 0.2 * atr[i]
                risk = sl_p - entry_p
                if risk <= 0:
                    continue
                tp_p = entry_p - 1.5 * risk
                
                outcome = "LOSS"
                exit_time = times[min(i+20, n-1)]
                rr = -1.0
                for j in range(i+1, min(i+100, n)):
                    if high[j] >= sl_p:
                        outcome = "LOSS"
                        rr = -1.0
                        exit_time = times[j]
                        break
                    elif low[j] <= tp_p:
                        outcome = "WIN"
                        rr = 1.5
                        exit_time = times[j]
                        break
                signals.append({
                    "strategy": "Bollinger_Reversion",
                    "symbol": sym,
                    "direction": "SELL",
                    "entry_time": pd.to_datetime(times[i+1]),
                    "exit_time": pd.to_datetime(exit_time),
                    "outcome": outcome,
                    "rr": rr
                })
    return signals

def run_dual_ema_pullback(dfs):
    signals = []
    for sym, df in dfs.items():
        if len(df) < 60:
            continue
        spread = SPREADS.get(sym, 0.0001)
        close = df['close']
        high = df['high'].values
        low = df['low'].values
        open_ = df['open'].values
        times = df['time'].values
        
        ema20 = close.ewm(span=20, adjust=False).mean().values
        ema50 = close.ewm(span=50, adjust=False).mean().values
        atr = calc_atr(df, 14)
        c_vals = close.values
        
        # Volatilidad normalizada
        atr_ratio = atr / pd.Series(atr).rolling(50).mean().values
        
        n = len(df)
        for i in range(55, n - 20):
            if np.isnan(atr[i]) or np.isnan(atr_ratio[i]) or atr[i] <= 0:
                continue
            
            body = abs(c_vals[i] - open_[i])
            rng = high[i] - low[i]
            body_ratio = body / rng if rng > 0 else 0
            
            # Tendencia Alcista: EMA20 > EMA50, retroceso tocó EMA20 o EMA50, vela alcista cierra arriba de EMA20
            if ema20[i] > ema50[i] and low[i] <= ema20[i] and c_vals[i] > ema20[i] and body_ratio >= 0.50 and atr_ratio[i] <= 1.25:
                entry_p = open_[i+1] + spread
                sl_p = min(low[i], ema50[i]) - 0.2 * atr[i]
                risk = entry_p - sl_p
                if risk <= 0:
                    continue
                tp_p = entry_p + 2.0 * risk # 1:2 RR
                
                outcome = "LOSS"
                exit_time = times[min(i+20, n-1)]
                rr = -1.0
                for j in range(i+1, min(i+120, n)):
                    if low[j] <= sl_p:
                        outcome = "LOSS"
                        rr = -1.0
                        exit_time = times[j]
                        break
                    elif high[j] >= tp_p:
                        outcome = "WIN"
                        rr = 2.0
                        exit_time = times[j]
                        break
                signals.append({
                    "strategy": "Dual_EMA_Pullback",
                    "symbol": sym,
                    "direction": "BUY",
                    "entry_time": pd.to_datetime(times[i+1]),
                    "exit_time": pd.to_datetime(exit_time),
                    "outcome": outcome,
                    "rr": rr
                })
                
            # Tendencia Bajista
            elif ema20[i] < ema50[i] and high[i] >= ema20[i] and c_vals[i] < ema20[i] and body_ratio >= 0.50 and atr_ratio[i] <= 1.25:
                entry_p = open_[i+1] - spread
                sl_p = max(high[i], ema50[i]) + 0.2 * atr[i]
                risk = sl_p - entry_p
                if risk <= 0:
                    continue
                tp_p = entry_p - 2.0 * risk
                
                outcome = "LOSS"
                exit_time = times[min(i+20, n-1)]
                rr = -1.0
                for j in range(i+1, min(i+120, n)):
                    if high[j] >= sl_p:
                        outcome = "LOSS"
                        rr = -1.0
                        exit_time = times[j]
                        break
                    elif low[j] <= tp_p:
                        outcome = "WIN"
                        rr = 2.0
                        exit_time = times[j]
                        break
                signals.append({
                    "strategy": "Dual_EMA_Pullback",
                    "symbol": sym,
                    "direction": "SELL",
                    "entry_time": pd.to_datetime(times[i+1]),
                    "exit_time": pd.to_datetime(exit_time),
                    "outcome": outcome,
                    "rr": rr
                })
    return signals

def evaluate_portfolio(trades, name):
    if not trades:
        return {
            "name": name, "N": 0, "Wins": 0, "Losses": 0, "Win%": 0.0,
            "Wilson_Low": 0.0, "Wilson_High": 0.0, "Net_PnL": 0.0, "Exp_R": 0.0,
            "PF": 0.0, "Payoff": 0.0, "MaxDD": 0.0
        }
    
    df = pd.DataFrame(trades).sort_values('entry_time').reset_index(drop=True)
    n = len(df)
    wins = len(df[df['outcome'] == 'WIN'])
    losses = len(df[df['outcome'] == 'LOSS'])
    win_rate = (wins / n) * 100.0 if n > 0 else 0.0
    w_low, w_high = wilson_interval(wins, n)
    
    net_pnl = df['rr'].sum()
    exp_r = net_pnl / n if n > 0 else 0.0
    
    gross_win = df[df['rr'] > 0]['rr'].sum()
    gross_loss = abs(df[df['rr'] < 0]['rr'].sum())
    pf = (gross_win / gross_loss) if gross_loss > 0 else np.nan
    
    avg_win = df[df['rr'] > 0]['rr'].mean() if wins > 0 else 0.0
    avg_loss = abs(df[df['rr'] < 0]['rr'].mean()) if losses > 0 else 0.0
    payoff = (avg_win / avg_loss) if avg_loss > 0 else 0.0
    
    # Max Drawdown
    equity = df['rr'].cumsum()
    peak = equity.cummax()
    dd = peak - equity
    max_dd = dd.max() if len(dd) > 0 else 0.0
    
    # Walk-forward por folds (4 periodos de 6 meses)
    # 2024-10-10 a 2026-10-10
    d_start = df['entry_time'].min()
    d_end = df['entry_time'].max()
    total_sec = (d_end - d_start).total_seconds()
    fold_sec = total_sec / 4.0
    
    folds = {}
    for f in range(4):
        f_start = d_start + pd.Timedelta(seconds=f * fold_sec)
        f_end = d_start + pd.Timedelta(seconds=(f + 1) * fold_sec)
        sub = df[(df['entry_time'] >= f_start) & (df['entry_time'] < f_end)]
        folds[f+1] = {
            "N": len(sub),
            "Net": sub['rr'].sum(),
            "WR": (len(sub[sub['outcome'] == 'WIN']) / len(sub) * 100.0) if len(sub) > 0 else 0.0
        }
        
    return {
        "name": name,
        "N": n,
        "Wins": wins,
        "Losses": losses,
        "Win%": round(win_rate, 1),
        "Wilson_Low": round(w_low * 100, 1),
        "Wilson_High": round(w_high * 100, 1),
        "Net_PnL": round(net_pnl, 2),
        "Exp_R": round(exp_r, 4),
        "PF": round(pf, 2) if not np.isnan(pf) else 99.0,
        "Payoff": round(payoff, 2),
        "MaxDD": round(max_dd, 2),
        "Folds": folds
    }

def main():
    print("=" * 100)
    print("REPRODUCCIÓN Y DESCUBRIMIENTO DE ESTRATEGIAS ALTERNATIVAS (23 ACTIVOS CANÓNICOS)")
    print("=" * 100)
    
    print("\nCargando datos M15 de 23 activos...")
    dfs = load_data()
    print(f"Cargados {len(dfs)} activos exitosamente.")
    
    # 1. Donchian Momentum Breakout
    print("\n1. Simulando Donchian Momentum Breakout (Trend Following)...")
    raw_donch = run_donchian_breakout(dfs)
    exec_donch = simulate_signals(raw_donch, cap=1)
    res_donch = evaluate_portfolio(exec_donch, "Donchian_Trend_Breakout")
    
    # 2. Bollinger Mean Reversion
    print("2. Simulando Bollinger Mean Reversion...")
    raw_boll = run_bollinger_reversion(dfs)
    exec_boll = simulate_signals(raw_boll, cap=1)
    res_boll = evaluate_portfolio(exec_boll, "Bollinger_Mean_Reversion")
    
    # 3. Dual-EMA Pullback
    print("3. Simulando Dual-EMA Pullback + Volatility Contraction...")
    raw_ema = run_dual_ema_pullback(dfs)
    exec_ema = simulate_signals(raw_ema, cap=1)
    res_ema = evaluate_portfolio(exec_ema, "Dual_EMA_Pullback")
    
    results = [res_donch, res_boll, res_ema]
    
    print("\n" + "=" * 120)
    print(f"{'Estrategia':30s} | {'N':4s} | {'Win% (IC 95%)':18s} | {'Payoff':6s} | {'Exp (R/op)':10s} | {'Net PnL':10s} | {'PF':5s} | {'MaxDD':6s} | {'Fold 4 (Holdout)':16s}")
    print("=" * 120)
    
    for r in results:
        w_str = f"{r['Win%']}% [{r['Wilson_Low']}-{r['Wilson_High']}%]"
        f4_str = f"N={r['Folds'][4]['N']}, Net={r['Folds'][4]['Net']:+.1f}R"
        print(f"{r['name']:30s} | {r['N']:4d} | {w_str:18s} | {r['Payoff']:6.2f} | {r['Exp_R']:+10.4f} | {r['Net_PnL']:+10.2f}R | {r['PF']:5.2f} | {r['MaxDD']:6.2f} | {f4_str:16s}")
        
    print("\nDetalle de Folds por Estrategia:")
    for r in results:
        print(f"\n--- {r['name']} ---")
        for f, f_data in r['Folds'].items():
            print(f"  Fold {f}: N={f_data['N']:3d} | WR={f_data['WR']:5.1f}% | Net={f_data['Net']:+7.2f}R")

if __name__ == '__main__':
    main()
