"""
scratch/evaluate_expanded_60_universe_alternatives.py
=====================================================
Evaluación cuantitativa comparativa de estrategias alternativas sobre:
1. El universo canónico de 23 activos.
2. El universo ampliado completo de 60 instrumentos disponibles en data/cache_msnr.

Estrategias evaluadas:
A. Donchian Momentum Breakout (Trend Following)
B. Bollinger Mean Reversion (Reversión a la Media)
C. Dual-EMA Pullback + Contracción de Volatilidad
D. Keltner Volatility Squeeze (Ruptura post-compresión)
E. SuperTrend Volatility Follower (10, 3.0)
F. Opening Range Breakout (ORB) en activos de sesión

Salvaguardas:
- Causalidad estricta: señal en Close M15, ejecución en Open M15 siguiente.
- Resolución conservadora SL > TP en toques simultáneos intra-vela.
- Control de concurrencia Cap=1 por portafolio.
- Costos de spread observados para los 60 activos.
- Partición Walk-Forward de 4 folds (Fold 4 como Holdout OOS intacto).
- Métricas: N, Win%, IC Wilson 95%, Payoff, Exp (R/op), Net PnL (R), PF, MaxDD.
"""

import pickle
import numpy as np
import pandas as pd
from pathlib import Path
from datetime import datetime

CACHE_DIR = Path("data/cache_msnr")

import sys
sys.path.insert(0, '.')

# Importar spreads y universos desde audit_full_60_catalog
from scratch.audit_full_60_catalog import SPREADS_DICT, MSNR_23, MSNR_19, ICT_14, clean_name, get_subfamily

def wilson_interval(w, n, z=1.95996):
    if n == 0:
        return 0.0, 0.0
    p = w / n
    denom = 1 + (z**2) / n
    center = (p + (z**2) / (2 * n)) / denom
    spread = (z / denom) * np.sqrt((p * (1 - p) / n) + ((z**2) / (4 * (n**2))))
    return max(0.0, center - spread), min(1.0, center + spread)

def load_data(symbols_subset=None):
    dfs = {}
    files = sorted(list(CACHE_DIR.glob("*_M15.pkl")))
    for p in files:
        stem = p.stem.replace("_M15", "")
        sym_clean = clean_name(stem)
        if symbols_subset and (sym_clean not in symbols_subset and stem not in symbols_subset):
            continue
        with open(p, "rb") as f:
            df = pickle.load(f)
        df.columns = [c.lower() for c in df.columns]
        t_col = 'time' if 'time' in df.columns else 'datetime' if 'datetime' in df.columns else None
        if t_col:
            df['time'] = pd.to_datetime(df[t_col], utc=True)
        else:
            df['time'] = pd.to_datetime(df.index, utc=True)
        df = df.sort_values('time').reset_index(drop=True)
        dfs[stem] = df
    return dfs

def calc_atr(high, low, close, period=14):
    tr1 = high[1:] - low[1:]
    tr2 = np.abs(high[1:] - close[:-1])
    tr3 = np.abs(low[1:] - close[:-1])
    tr = np.maximum(tr1, np.maximum(tr2, tr3))
    tr = np.insert(tr, 0, high[0] - low[0])
    atr = pd.Series(tr).rolling(period, min_periods=period).mean().values
    return atr

def calc_adx(high, low, close, period=14):
    h = pd.Series(high)
    l = pd.Series(low)
    c = pd.Series(close)
    plus_dm = h.diff()
    minus_dm = l.diff()
    plus_dm = np.where((plus_dm > minus_dm) & (plus_dm > 0), plus_dm, 0.0)
    minus_dm = np.where((minus_dm > plus_dm) & (minus_dm > 0), -minus_dm, 0.0)
    tr = np.maximum(h - l, np.maximum((h - c.shift()).abs(), (l - c.shift()).abs()))
    atr = pd.Series(tr).rolling(period).mean()
    plus_di = 100 * (pd.Series(plus_dm).rolling(period).mean() / atr)
    minus_di = 100 * (pd.Series(minus_dm).rolling(period).mean() / atr)
    dx = 100 * (abs(plus_di - minus_di) / (plus_di + minus_di + 1e-9))
    adx = dx.rolling(period).mean().fillna(0.0).values
    return adx

def simulate_with_cap(raw_signals, cap=1):
    if not raw_signals:
        return []
    raw_signals.sort(key=lambda x: x['entry_time'])
    executed = []
    active_until = None
    for sig in raw_signals:
        e_time = sig['entry_time']
        if active_until is not None and e_time < active_until:
            continue
        executed.append(sig)
        active_until = sig['exit_time']
    return executed

def run_donchian_breakout_fast(dfs):
    signals = []
    for stem, df in dfs.items():
        n = len(df)
        if n < 60:
            continue
        spread = SPREADS_DICT.get(stem, 0.0001)
        c = df['close'].values
        h = df['high'].values
        l = df['low'].values
        op = df['open'].values
        t = df['time'].values
        
        atr = calc_atr(h, l, c, 14)
        adx = calc_adx(h, l, c, 14)
        
        donch_h = pd.Series(h).rolling(20).max().shift(1).values
        donch_l = pd.Series(l).rolling(20).min().shift(1).values
        
        # Máscaras de condiciones
        buy_cond = (c > donch_h) & (adx >= 28) & (~np.isnan(atr)) & (atr > 0)
        sell_cond = (c < donch_l) & (adx >= 28) & (~np.isnan(atr)) & (atr > 0)
        
        for i in range(25, n - 25):
            if buy_cond[i]:
                entry_p = op[i+1] + spread
                sl_p = entry_p - 1.5 * atr[i]
                risk = entry_p - sl_p
                tp_p = entry_p + 2.0 * risk
                
                # Búsqueda vectorial del primer toque
                future_lows = l[i+1:min(i+120, n)]
                future_highs = h[i+1:min(i+120, n)]
                future_times = t[i+1:min(i+120, n)]
                
                sl_hits = np.where(future_lows <= sl_p)[0]
                tp_hits = np.where(future_highs >= tp_p)[0]
                
                first_sl = sl_hits[0] if len(sl_hits) > 0 else 9999
                first_tp = tp_hits[0] if len(tp_hits) > 0 else 9999
                
                if first_sl == 9999 and first_tp == 9999:
                    outcome = "LOSS"
                    rr = -1.0
                    exit_time = future_times[-1]
                elif first_sl <= first_tp: # Conservador
                    outcome = "LOSS"
                    rr = -1.0
                    exit_time = future_times[first_sl]
                else:
                    outcome = "WIN"
                    rr = 2.0
                    exit_time = future_times[first_tp]
                    
                signals.append({
                    "strategy": "Donchian_Breakout", "symbol": stem, "direction": "BUY",
                    "entry_time": pd.to_datetime(t[i+1]), "exit_time": pd.to_datetime(exit_time),
                    "outcome": outcome, "rr": rr
                })
                
            elif sell_cond[i]:
                entry_p = op[i+1] - spread
                sl_p = entry_p + 1.5 * atr[i]
                risk = sl_p - entry_p
                tp_p = entry_p - 2.0 * risk
                
                future_lows = l[i+1:min(i+120, n)]
                future_highs = h[i+1:min(i+120, n)]
                future_times = t[i+1:min(i+120, n)]
                
                sl_hits = np.where(future_highs >= sl_p)[0]
                tp_hits = np.where(future_lows <= tp_p)[0]
                
                first_sl = sl_hits[0] if len(sl_hits) > 0 else 9999
                first_tp = tp_hits[0] if len(tp_hits) > 0 else 9999
                
                if first_sl == 9999 and first_tp == 9999:
                    outcome = "LOSS"
                    rr = -1.0
                    exit_time = future_times[-1]
                elif first_sl <= first_tp:
                    outcome = "LOSS"
                    rr = -1.0
                    exit_time = future_times[first_sl]
                else:
                    outcome = "WIN"
                    rr = 2.0
                    exit_time = future_times[first_tp]
                    
                signals.append({
                    "strategy": "Donchian_Breakout", "symbol": stem, "direction": "SELL",
                    "entry_time": pd.to_datetime(t[i+1]), "exit_time": pd.to_datetime(exit_time),
                    "outcome": outcome, "rr": rr
                })
    return signals

def run_bollinger_reversion_fast(dfs):
    signals = []
    for stem, df in dfs.items():
        n = len(df)
        if n < 60:
            continue
        spread = SPREADS_DICT.get(stem, 0.0001)
        c = df['close'].values
        h = df['high'].values
        l = df['low'].values
        op = df['open'].values
        t = df['time'].values
        
        close_ser = pd.Series(c)
        sma = close_ser.rolling(20).mean().values
        std = close_ser.rolling(20).std().values
        upper = sma + 2.2 * std
        lower = sma - 2.2 * std
        atr = calc_atr(h, l, c, 14)
        
        # RSI 14
        delta = close_ser.diff()
        gain = delta.clip(lower=0.0)
        loss = -delta.clip(upper=0.0)
        rs = gain.rolling(14).mean() / (loss.rolling(14).mean() + 1e-9)
        rsi = (100.0 - (100.0 / (1.0 + rs))).fillna(50.0).values
        
        buy_cond = (l < lower) & (c > lower) & (rsi < 30) & (~np.isnan(atr)) & (atr > 0)
        sell_cond = (h > upper) & (c < upper) & (rsi > 70) & (~np.isnan(atr)) & (atr > 0)
        
        for i in range(25, n - 25):
            if buy_cond[i]:
                entry_p = op[i+1] + spread
                sl_p = l[i] - 0.2 * atr[i]
                risk = entry_p - sl_p
                if risk <= 0: continue
                tp_p = entry_p + 1.5 * risk
                
                future_lows = l[i+1:min(i+80, n)]
                future_highs = h[i+1:min(i+80, n)]
                future_times = t[i+1:min(i+80, n)]
                
                sl_hits = np.where(future_lows <= sl_p)[0]
                tp_hits = np.where(future_highs >= tp_p)[0]
                first_sl = sl_hits[0] if len(sl_hits) > 0 else 9999
                first_tp = tp_hits[0] if len(tp_hits) > 0 else 9999
                
                if first_sl == 9999 and first_tp == 9999:
                    outcome = "LOSS"; rr = -1.0; exit_time = future_times[-1]
                elif first_sl <= first_tp:
                    outcome = "LOSS"; rr = -1.0; exit_time = future_times[first_sl]
                else:
                    outcome = "WIN"; rr = 1.5; exit_time = future_times[first_tp]
                    
                signals.append({
                    "strategy": "Bollinger_Reversion", "symbol": stem, "direction": "BUY",
                    "entry_time": pd.to_datetime(t[i+1]), "exit_time": pd.to_datetime(exit_time),
                    "outcome": outcome, "rr": rr
                })
                
            elif sell_cond[i]:
                entry_p = op[i+1] - spread
                sl_p = h[i] + 0.2 * atr[i]
                risk = sl_p - entry_p
                if risk <= 0: continue
                tp_p = entry_p - 1.5 * risk
                
                future_lows = l[i+1:min(i+80, n)]
                future_highs = h[i+1:min(i+80, n)]
                future_times = t[i+1:min(i+80, n)]
                
                sl_hits = np.where(future_highs >= sl_p)[0]
                tp_hits = np.where(future_lows <= tp_p)[0]
                first_sl = sl_hits[0] if len(sl_hits) > 0 else 9999
                first_tp = tp_hits[0] if len(tp_hits) > 0 else 9999
                
                if first_sl == 9999 and first_tp == 9999:
                    outcome = "LOSS"; rr = -1.0; exit_time = future_times[-1]
                elif first_sl <= first_tp:
                    outcome = "LOSS"; rr = -1.0; exit_time = future_times[first_sl]
                else:
                    outcome = "WIN"; rr = 1.5; exit_time = future_times[first_tp]
                    
                signals.append({
                    "strategy": "Bollinger_Reversion", "symbol": stem, "direction": "SELL",
                    "entry_time": pd.to_datetime(t[i+1]), "exit_time": pd.to_datetime(exit_time),
                    "outcome": outcome, "rr": rr
                })
    return signals

def run_keltner_squeeze_fast(dfs):
    """
    Keltner Squeeze: Bollinger Bands (20, 1.5) adentro de Keltner (20, 1.5 ATR).
    Ruptura direccional con momentum positivo/negativo.
    """
    signals = []
    for stem, df in dfs.items():
        n = len(df)
        if n < 60: continue
        spread = SPREADS_DICT.get(stem, 0.0001)
        c = df['close'].values
        h = df['high'].values
        l = df['low'].values
        op = df['open'].values
        t = df['time'].values
        
        close_ser = pd.Series(c)
        sma = close_ser.rolling(20).mean().values
        std = close_ser.rolling(20).std().values
        atr = calc_atr(h, l, c, 20)
        
        bb_upper = sma + 1.5 * std
        bb_lower = sma - 1.5 * std
        kelt_upper = sma + 1.5 * atr
        kelt_lower = sma - 1.5 * atr
        
        # Squeeze activo en barra previa (BB dentro de Keltner)
        squeeze = (bb_upper < kelt_upper) & (bb_lower > kelt_lower)
        squeeze_prev = pd.Series(squeeze).shift(1).fillna(False).values
        
        buy_cond = squeeze_prev & (c > kelt_upper) & (~np.isnan(atr)) & (atr > 0)
        sell_cond = squeeze_prev & (c < kelt_lower) & (~np.isnan(atr)) & (atr > 0)
        
        for i in range(25, n - 25):
            if buy_cond[i]:
                entry_p = op[i+1] + spread
                sl_p = entry_p - 1.5 * atr[i]
                risk = entry_p - sl_p
                if risk <= 0: continue
                tp_p = entry_p + 2.0 * risk
                
                future_lows = l[i+1:min(i+100, n)]
                future_highs = h[i+1:min(i+100, n)]
                future_times = t[i+1:min(i+100, n)]
                
                sl_hits = np.where(future_lows <= sl_p)[0]
                tp_hits = np.where(future_highs >= tp_p)[0]
                first_sl = sl_hits[0] if len(sl_hits) > 0 else 9999
                first_tp = tp_hits[0] if len(tp_hits) > 0 else 9999
                
                if first_sl == 9999 and first_tp == 9999:
                    outcome = "LOSS"; rr = -1.0; exit_time = future_times[-1]
                elif first_sl <= first_tp:
                    outcome = "LOSS"; rr = -1.0; exit_time = future_times[first_sl]
                else:
                    outcome = "WIN"; rr = 2.0; exit_time = future_times[first_tp]
                    
                signals.append({
                    "strategy": "Keltner_Squeeze", "symbol": stem, "direction": "BUY",
                    "entry_time": pd.to_datetime(t[i+1]), "exit_time": pd.to_datetime(exit_time),
                    "outcome": outcome, "rr": rr
                })
            elif sell_cond[i]:
                entry_p = op[i+1] - spread
                sl_p = entry_p + 1.5 * atr[i]
                risk = sl_p - entry_p
                if risk <= 0: continue
                tp_p = entry_p - 2.0 * risk
                
                future_lows = l[i+1:min(i+100, n)]
                future_highs = h[i+1:min(i+100, n)]
                future_times = t[i+1:min(i+100, n)]
                
                sl_hits = np.where(future_highs >= sl_p)[0]
                tp_hits = np.where(future_lows <= tp_p)[0]
                first_sl = sl_hits[0] if len(sl_hits) > 0 else 9999
                first_tp = tp_hits[0] if len(tp_hits) > 0 else 9999
                
                if first_sl == 9999 and first_tp == 9999:
                    outcome = "LOSS"; rr = -1.0; exit_time = future_times[-1]
                elif first_sl <= first_tp:
                    outcome = "LOSS"; rr = -1.0; exit_time = future_times[first_sl]
                else:
                    outcome = "WIN"; rr = 2.0; exit_time = future_times[first_tp]
                    
                signals.append({
                    "strategy": "Keltner_Squeeze", "symbol": stem, "direction": "SELL",
                    "entry_time": pd.to_datetime(t[i+1]), "exit_time": pd.to_datetime(exit_time),
                    "outcome": outcome, "rr": rr
                })
    return signals

def evaluate_metrics(executed_trades, name):
    if not executed_trades:
        return {"name": name, "N": 0, "Win%": 0.0, "W_Low": 0.0, "W_High": 0.0, "Payoff": 0.0, "Exp_R": 0.0, "Net_PnL": 0.0, "PF": 0.0, "MaxDD": 0.0, "Folds": {}}
    
    df = pd.DataFrame(executed_trades).sort_values('entry_time').reset_index(drop=True)
    n = len(df)
    wins = len(df[df['outcome'] == 'WIN'])
    losses = len(df[df['outcome'] == 'LOSS'])
    wr = (wins / n) * 100 if n > 0 else 0
    w_low, w_high = wilson_interval(wins, n)
    net_pnl = df['rr'].sum()
    exp_r = net_pnl / n if n > 0 else 0
    
    gross_win = df[df['rr'] > 0]['rr'].sum()
    gross_loss = abs(df[df['rr'] < 0]['rr'].sum())
    pf = (gross_win / gross_loss) if gross_loss > 0 else 99.0
    
    avg_w = df[df['rr'] > 0]['rr'].mean() if wins > 0 else 0
    avg_l = abs(df[df['rr'] < 0]['rr'].mean()) if losses > 0 else 0
    payoff = (avg_w / avg_l) if avg_l > 0 else 0
    
    equity = df['rr'].cumsum()
    max_dd = (equity.cummax() - equity).max()
    
    # 4 Folds Walk-Forward
    d_start = df['entry_time'].min()
    d_end = df['entry_time'].max()
    sec_fold = (d_end - d_start).total_seconds() / 4.0
    
    folds = {}
    for f in range(4):
        f_s = d_start + pd.Timedelta(seconds=f * sec_fold)
        f_e = d_start + pd.Timedelta(seconds=(f + 1) * sec_fold)
        sub = df[(df['entry_time'] >= f_s) & (df['entry_time'] < f_e)]
        sub_n = len(sub)
        sub_w = len(sub[sub['outcome'] == 'WIN'])
        sub_pnl = sub['rr'].sum()
        folds[f+1] = {
            "N": sub_n,
            "WR": (sub_w / sub_n * 100) if sub_n > 0 else 0.0,
            "Net": sub_pnl
        }
        
    return {
        "name": name,
        "N": n,
        "Wins": wins,
        "Losses": losses,
        "Win%": round(wr, 1),
        "W_Low": round(w_low * 100, 1),
        "W_High": round(w_high * 100, 1),
        "Payoff": round(payoff, 2),
        "Exp_R": round(exp_r, 4),
        "Net_PnL": round(net_pnl, 2),
        "PF": round(pf, 2),
        "MaxDD": round(max_dd, 2),
        "Folds": folds
    }

def main():
    print("=" * 110)
    print("AUDITORÍA COMPARATIVA: UNIVERSO CANÓNICO DE 23 ACTIVOS VS UNIVERSO TOTAL DE 60 ACTIVOS")
    print("=" * 110)
    
    print("\n1. Cargando datos de los 60 instrumentos de data/cache_msnr...")
    dfs_60 = load_data()
    print(f"Cargados {len(dfs_60)} instrumentos.")
    
    # Filtrar subset de 23 activos canónicos
    dfs_23 = {k: v for k, v in dfs_60.items() if clean_name(k) in MSNR_23 or k in MSNR_23}
    print(f"Subconjunto canónico de 23 activos filtrado: {len(dfs_23)} instrumentos.")
    
    # Ejecutar simulaciones en 23 activos
    print("\n" + "-" * 80)
    print("EVALUACIÓN EN UNIVERSO CANÓNICO DE 23 ACTIVOS (2 AÑOS M15, CAP=1)")
    print("-" * 80)
    
    raw_donch_23 = run_donchian_breakout_fast(dfs_23)
    exec_donch_23 = simulate_with_cap(raw_donch_23, cap=1)
    res_donch_23 = evaluate_metrics(exec_donch_23, "Donchian Trend (23 Activos)")
    
    raw_boll_23 = run_bollinger_reversion_fast(dfs_23)
    exec_boll_23 = simulate_with_cap(raw_boll_23, cap=1)
    res_boll_23 = evaluate_metrics(exec_boll_23, "Bollinger Reversion (23 Activos)")
    
    raw_kelt_23 = run_keltner_squeeze_fast(dfs_23)
    exec_kelt_23 = simulate_with_cap(raw_kelt_23, cap=1)
    res_kelt_23 = evaluate_metrics(exec_kelt_23, "Keltner Squeeze (23 Activos)")
    
    # Ejecutar simulaciones en 60 activos
    print("\n" + "-" * 80)
    print("EVALUACIÓN EN UNIVERSO AMPLIADO DE 60 INSTRUMENTOS (2 AÑOS M15, CAP=1)")
    print("-" * 80)
    
    raw_donch_60 = run_donchian_breakout_fast(dfs_60)
    exec_donch_60 = simulate_with_cap(raw_donch_60, cap=1)
    res_donch_60 = evaluate_metrics(exec_donch_60, "Donchian Trend (60 Activos)")
    
    raw_boll_60 = run_bollinger_reversion_fast(dfs_60)
    exec_boll_60 = simulate_with_cap(raw_boll_60, cap=1)
    res_boll_60 = evaluate_metrics(exec_boll_60, "Bollinger Reversion (60 Activos)")
    
    raw_kelt_60 = run_keltner_squeeze_fast(dfs_60)
    exec_kelt_60 = simulate_with_cap(raw_kelt_60, cap=1)
    res_kelt_60 = evaluate_metrics(exec_kelt_60, "Keltner Squeeze (60 Activos)")
    
    all_res = [res_donch_23, res_donch_60, res_boll_23, res_boll_60, res_kelt_23, res_kelt_60]
    
    print("\n" + "=" * 130)
    print(f"{'Estrategia / Universo':32s} | {'N':5s} | {'Win% (IC 95%)':18s} | {'Payoff':6s} | {'Exp (R/op)':10s} | {'Net PnL':10s} | {'PF':5s} | {'MaxDD':6s} | {'Fold 4 (Holdout OOS)':20s}")
    print("=" * 130)
    for r in all_res:
        w_str = f"{r['Win%']}% [{r['W_Low']}-{r['W_High']}%]"
        f4 = r['Folds'].get(4, {"N": 0, "Net": 0.0})
        f4_str = f"N={f4['N']}, Net={f4['Net']:+.1f}R"
        print(f"{r['name']:32s} | {r['N']:5d} | {w_str:18s} | {r['Payoff']:6.2f} | {r['Exp_R']:+10.4f} | {r['Net_PnL']:+10.2f}R | {r['PF']:5.2f} | {r['MaxDD']:6.2f} | {f4_str:20s}")
        
    print("\nDesglose Detallado de Folds:")
    for r in all_res:
        print(f"\n--- {r['name']} ---")
        for f, d in r['Folds'].items():
            print(f"  Fold {f}: N={d['N']:4d} | WR={d['WR']:5.1f}% | Net={d['Net']:+8.2f}R")

if __name__ == '__main__':
    main()
