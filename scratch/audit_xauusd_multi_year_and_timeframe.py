"""
scratch/audit_xauusd_multi_year_and_timeframe.py
================================================
Estudio independiente y separado de XAUUSD (Oro):
1. Replay M15 sobre el historial máximo local de 4.24 años (data/historical/XAUUSD_M15.csv: 100,000 barras, 2022-07 a 2026-10).
2. Estudio separado en H1 sobre 6.79 años (data/historical/XAUUSD_H1.csv: 40,000 barras, 2019-12 a 2026-10).
3. Demostración técnica de por qué H1 NO es equivalente ni sustituto de M15.
4. Confirmación de que XAUUSD 4.24y M15 es un estudio aislado y NO representa el portafolio canónico completo de 23 activos.
"""

import sys
import pandas as pd
import numpy as np
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent

def calculate_atr(df: pd.DataFrame, period: int = 14) -> pd.Series:
    high = df['high']
    low = df['low']
    close_prev = df['close'].shift(1)
    tr1 = high - low
    tr2 = (high - close_prev).abs()
    tr3 = (low - close_prev).abs()
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    return tr.rolling(period).mean()

def calculate_adx(df: pd.DataFrame, period: int = 14) -> pd.Series:
    high = df['high']
    low = df['low']
    close = df['close']
    plus_dm = high.diff()
    minus_dm = low.diff().abs()
    plus_dm = np.where((plus_dm > minus_dm) & (plus_dm > 0), plus_dm, 0.0)
    minus_dm = np.where((minus_dm > plus_dm) & (minus_dm > 0), minus_dm, 0.0)
    
    tr1 = high - low
    tr2 = (high - close.shift(1)).abs()
    tr3 = (low - close.shift(1)).abs()
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    atr = tr.rolling(period).mean()
    
    plus_di = 100 * (pd.Series(plus_dm, index=df.index).rolling(period).mean() / atr)
    minus_di = 100 * (pd.Series(minus_dm, index=df.index).rolling(period).mean() / atr)
    dx = (abs(plus_di - minus_di) / (plus_di + minus_di + 1e-9)) * 100
    adx = dx.rolling(period).mean()
    return adx

def simulate_simple_msnr_on_bars(csv_path: Path, tf_name: str, spread_pts: float = 0.25):
    print(f"\n--- Analizando {tf_name} desde {csv_path.name} ---")
    df = pd.read_csv(csv_path)
    df['time'] = pd.to_datetime(df['time'], utc=True)
    df = df.sort_values('time').reset_index(drop=True)
    
    print(f"Total barras: {len(df):,}")
    print(f"Rango de fechas: {df['time'].iloc[0]} a {df['time'].iloc[-1]} ({(df['time'].iloc[-1] - df['time'].iloc[0]).days / 365.25:.2f} años)")
    
    df['atr'] = calculate_atr(df, 14)
    df['adx'] = calculate_adx(df, 14)
    
    # Simulación de fractales simplificada para comparar M15 vs H1
    # Swing high / low de 5 barras
    df['swing_high'] = (df['high'] == df['high'].rolling(5, center=True).max())
    df['swing_low'] = (df['low'] == df['low'].rolling(5, center=True).min())
    
    trades = []
    # Señales: Quasimodo / Fractal break
    for i in range(20, len(df) - 1):
        row = df.iloc[i]
        next_bar = df.iloc[i+1]
        
        # Filtros V4
        if row['adx'] < 30.0 or row['atr'] <= 0:
            continue
            
        # Señal Buy si rompe swing high reciente
        if row['close'] > df['high'].iloc[i-5:i].max():
            sl = row['low'] - 0.5 * row['atr']
            risk = (row['close'] - sl)
            if risk <= 0: continue
            risk_atr = risk / row['atr']
            if risk_atr > 1.5: continue
            
            entry = next_bar['open'] + spread_pts
            tp = entry + 2.5 * risk
            
            # Evaluar salida en barras posteriores
            outcome = None
            bars_held = 0
            for j in range(i+1, min(len(df), i+1+150)):
                b = df.iloc[j]
                bars_held += 1
                hit_sl = b['low'] <= sl
                hit_tp = b['high'] >= tp
                if hit_sl and hit_tp:
                    outcome = 'SL_TIE'
                    rr = -1.0
                    break
                elif hit_sl:
                    outcome = 'SL'
                    rr = -1.0
                    break
                elif hit_tp:
                    outcome = 'TP'
                    rr = 2.5
                    break
            if outcome is None:
                outcome = 'TIMEOUT'
                rr = (df.iloc[min(len(df)-1, i+150)]['close'] - entry) / risk
            trades.append({'time': row['time'], 'direction': 'BUY', 'rr': rr, 'outcome': outcome, 'bars': bars_held})
            
        # Señal Sell si rompe swing low reciente
        elif row['close'] < df['low'].iloc[i-5:i].min():
            sl = row['high'] + 0.5 * row['atr']
            risk = (sl - row['close'])
            if risk <= 0: continue
            risk_atr = risk / row['atr']
            if risk_atr > 1.5: continue
            
            entry = next_bar['open'] - spread_pts
            tp = entry - 2.5 * risk
            
            outcome = None
            bars_held = 0
            for j in range(i+1, min(len(df), i+1+150)):
                b = df.iloc[j]
                bars_held += 1
                hit_sl = b['high'] >= sl
                hit_tp = b['low'] <= tp
                if hit_sl and hit_tp:
                    outcome = 'SL_TIE'
                    rr = -1.0
                    break
                elif hit_sl:
                    outcome = 'SL'
                    rr = -1.0
                    break
                elif hit_tp:
                    outcome = 'TP'
                    rr = 2.5
                    break
            if outcome is None:
                outcome = 'TIMEOUT'
                rr = (entry - df.iloc[min(len(df)-1, i+150)]['close']) / risk
            trades.append({'time': row['time'], 'direction': 'SELL', 'rr': rr, 'outcome': outcome, 'bars': bars_held})

    tdf = pd.DataFrame(trades)
    if len(tdf) > 0:
        # Simular Cap=1
        acc = []
        last_exit = None
        for _, tr in tdf.iterrows():
            t_entry = tr['time']
            if last_exit is None or t_entry >= last_exit:
                acc.append(tr)
                # Estimación de salida
                last_exit = t_entry + pd.Timedelta(minutes=tr['bars'] * (15 if 'M15' in tf_name else 60))
        acc_df = pd.DataFrame(acc)
        
        n = len(acc_df)
        wins = acc_df[acc_df['rr'] > 0]
        losses = acc_df[acc_df['rr'] <= 0]
        wr = len(wins) / n * 100
        net = acc_df['rr'].sum()
        gw = wins['rr'].sum()
        gl = abs(losses['rr'].sum())
        pf = gw / gl if gl > 0 else 99.0
        print(f"Resultados {tf_name} (Cap=1): N={n} | WR={wr:.1f}% | Net R={net:+.2f}R | PF={pf:.2f}")
    else:
        print(f"Sin operaciones en {tf_name}")

if __name__ == '__main__':
    simulate_simple_msnr_on_bars(PROJECT_ROOT / 'data/historical/XAUUSD_M15.csv', 'XAUUSD M15 (4.24 años)')
    simulate_simple_msnr_on_bars(PROJECT_ROOT / 'data/historical/XAUUSD_H1.csv', 'XAUUSD H1 (6.79 años)')
