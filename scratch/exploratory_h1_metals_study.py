"""
scratch/exploratory_h1_metals_study.py
Estudio Exploratorio Independiente de Malaysian SNR en Metales (H1, 2019–2026, ~6.8 Años).

OBJETIVO METODOLÓGICO:
- Evaluar el comportamiento de las reglas Malaysian SNR (Break / Retest de A/V con filtro ADX y ATR)
  sobre el único activo local con más de 5 años continuos de datos históricos (XAUUSD y XAGUSD en H1).
- IMPORTANTE: Este estudio es estrictamente exploratorio e independiente. NO sustituye ni equivale
  al replay M15 del portafolio canónico, y no puede utilizarse para validar el portafolio completo
  de 23 activos (el cual contiene un 65% de índices sintéticos de Deriv sin datos de 5 años).
"""

import pandas as pd
import numpy as np
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent

def compute_atr(df: pd.DataFrame, period: int = 14) -> pd.Series:
    prev_close = df["close"].shift(1)
    tr = pd.concat([
        df["high"] - df["low"],
        (df["high"] - prev_close).abs(),
        (df["low"] - prev_close).abs(),
    ], axis=1).max(axis=1)
    return tr.rolling(period).mean()

def compute_adx(df: pd.DataFrame, period: int = 14) -> pd.Series:
    high = df["high"]
    low = df["low"]
    close = df["close"]
    prev_close = close.shift(1)
    tr = pd.concat([
        high - low,
        (high - prev_close).abs(),
        (low - prev_close).abs(),
    ], axis=1).max(axis=1)
    up_move = high - high.shift(1)
    down_move = low.shift(1) - low
    plus_dm = np.where((up_move > down_move) & (up_move > 0), up_move, 0.0)
    minus_dm = np.where((down_move > up_move) & (down_move > 0), down_move, 0.0)
    atr = tr.rolling(period).mean()
    plus_di = 100 * (pd.Series(plus_dm, index=df.index).rolling(period).mean() / atr)
    minus_di = 100 * (pd.Series(minus_dm, index=df.index).rolling(period).mean() / atr)
    dx = 100 * (abs(plus_di - minus_di) / (plus_di + minus_di).replace(0, np.nan))
    adx = dx.rolling(period).mean()
    return adx

def simulate_h1_snr(csv_path: Path, symbol_name: str):
    df = pd.read_csv(csv_path)
    df['time'] = pd.to_datetime(df['time'], utc=True)
    df = df.sort_values('time').reset_index(drop=True)
    
    df['atr'] = compute_atr(df, 14)
    df['adx'] = compute_adx(df, 14)
    
    # Detección de patrones A / V (Resistencia / Soporte) en H1
    # V-pattern (Soporte): vela bajista seguida de envolvente alcista
    # A-pattern (Resistencia): vela alcista seguida de envolvente bajista
    signals = []
    
    for i in range(20, len(df) - 50):
        c_prev = df.loc[i-1, 'close']
        o_prev = df.loc[i-1, 'open']
        c_curr = df.loc[i, 'close']
        o_curr = df.loc[i, 'open']
        h_curr = df.loc[i, 'high']
        l_curr = df.loc[i, 'low']
        atr_val = df.loc[i, 'atr']
        adx_val = df.loc[i, 'adx']
        
        if pd.isna(atr_val) or pd.isna(adx_val) or atr_val <= 0:
            continue
            
        # V-pattern Buy Signal: Envolvente alcista que rompe el open de la vela bajista previa
        is_v_pattern = (c_prev < o_prev) and (c_curr > o_curr) and (c_curr > o_prev)
        # A-pattern Sell Signal: Envolvente bajista que rompe el open de la vela alcista previa
        is_a_pattern = (c_prev > o_prev) and (c_curr < o_curr) and (c_curr < o_prev)
        
        # Filtro de Régimen: ADX >= 30
        if is_v_pattern and adx_val >= 30.0:
            entry = df.loc[i+1, 'open']
            sl = min(df.loc[i-1, 'low'], l_curr)
            risk = entry - sl
            if 0 < risk <= 1.5 * atr_val:
                tp1 = entry + 2.0 * risk
                signals.append({
                    "time": df.loc[i+1, 'time'], "symbol": symbol_name, "direction": "BUY",
                    "entry": entry, "sl": sl, "tp1": tp1, "risk": risk, "atr": atr_val,
                    "adx": adx_val, "idx": i + 1
                })
        elif is_a_pattern and adx_val >= 30.0:
            entry = df.loc[i+1, 'open']
            sl = max(df.loc[i-1, 'high'], h_curr)
            risk = sl - entry
            if 0 < risk <= 1.5 * atr_val:
                tp1 = entry - 2.0 * risk
                signals.append({
                    "time": df.loc[i+1, 'time'], "symbol": symbol_name, "direction": "SELL",
                    "entry": entry, "sl": sl, "tp1": tp1, "risk": risk, "atr": atr_val,
                    "adx": adx_val, "idx": i + 1
                })
                
    sig_df = pd.DataFrame(signals)
    if len(sig_df) == 0:
        print(f"[{symbol_name} H1] No se generaron señales.")
        return
        
    # Evaluación de resultados (Hold máximo 50 barras)
    results = []
    for _, s in sig_df.iterrows():
        idx = int(s['idx'])
        dir_ = s['direction']
        entry = s['entry']
        sl = s['sl']
        tp = s['tp1']
        
        outcome_r = 0.0
        hit = False
        for j in range(idx, min(len(df), idx + 50)):
            h = df.loc[j, 'high']
            l = df.loc[j, 'low']
            
            if dir_ == 'BUY':
                # Pesimista: si toca ambos en la misma vela, gana SL
                if l <= sl and h >= tp:
                    outcome_r = -1.0
                    hit = True
                    break
                elif l <= sl:
                    outcome_r = -1.0
                    hit = True
                    break
                elif h >= tp:
                    outcome_r = 2.0
                    hit = True
                    break
            else: # SELL
                if h >= sl and l <= tp:
                    outcome_r = -1.0
                    hit = True
                    break
                elif h >= sl:
                    outcome_r = -1.0
                    hit = True
                    break
                elif l <= tp:
                    outcome_r = 2.0
                    hit = True
                    break
        if not hit:
            # Cierre por tiempo
            last_c = df.loc[min(len(df)-1, idx+49), 'close']
            outcome_r = (last_c - entry) / s['risk'] if dir_ == 'BUY' else (entry - last_c) / s['risk']
            
        results.append(outcome_r)
        
    sig_df['rr'] = results
    
    # Métricas
    n = len(sig_df)
    nw = (sig_df['rr'] > 0).sum()
    nl = (sig_df['rr'] <= 0).sum()
    wr = nw / n * 100
    net_r = sig_df['rr'].sum()
    exp_r = sig_df['rr'].mean()
    tot_g = sig_df[sig_df['rr'] > 0]['rr'].sum()
    tot_l = abs(sig_df[sig_df['rr'] <= 0]['rr'].sum())
    pf = tot_g / tot_l if tot_l > 0 else 99.0
    cum = sig_df['rr'].cumsum()
    max_dd = (cum.cummax() - cum).max()
    
    t_start = sig_df['time'].min().strftime('%Y-%m-%d')
    t_end = sig_df['time'].max().strftime('%Y-%m-%d')
    days = (sig_df['time'].max() - sig_df['time'].min()).days
    
    print("=" * 105)
    print(f"ESTUDIO EXPLORATORIO INDEPENDIENTE: {symbol_name} en H1 ({t_start} a {t_end}, {days} días / {days/365.25:.1f} años)")
    print("=" * 105)
    print(f"  * Operaciones Totales (N): {n}")
    print(f"  * Tasa de Acierto (Win Rate): {wr:.1f}% ({nw} Wins / {nl} Losses)")
    print(f"  * PnL Neto en R: {net_r:+.2f} R")
    print(f"  * Expectativa por Operación: {exp_r:+.4f} R/op")
    print(f"  * Profit Factor (PF): {pf:.2f}")
    print(f"  * Max Drawdown: {max_dd:.2f} R")
    print(f"  * Advertencia: Estudio H1 exploratorio. NO equivale a la estrategia M15 ni al portafolio canónico.")

def main():
    p_xau = PROJECT_ROOT / "data" / "historical" / "XAUUSD_H1.csv"
    p_xag = PROJECT_ROOT / "data" / "historical" / "XAGUSD_H1.csv"
    
    if p_xau.exists():
        simulate_h1_snr(p_xau, "XAUUSD")
    if p_xag.exists():
        simulate_h1_snr(p_xag, "XAGUSD")

if __name__ == '__main__':
    main()
