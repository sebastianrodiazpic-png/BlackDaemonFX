"""Audit Toby Crabel NR7 and Inside Day on ORB enabled universe."""
import sys
from pathlib import Path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import pandas as pd
import numpy as np

def compute_daily_ranges(symbol):
    clean_sym = symbol.replace(" ", "_")
    h1_path = PROJECT_ROOT / f"data/historical/{clean_sym}_H1.csv"
    if not h1_path.exists():
        h1_path = PROJECT_ROOT / f"data/forex_historical/{clean_sym}_H1.csv"
    if not h1_path.exists():
        return None
        
    df = pd.read_csv(h1_path)
    time_col = [c for c in df.columns if 'time' in c.lower() or 'date' in c.lower()][0]
    df['time'] = pd.to_datetime(df[time_col], utc=True)
    df = df.sort_values('time').reset_index(drop=True)
    
    # Resample to Daily (D)
    df.set_index('time', inplace=True)
    daily = df.resample('1D').agg({
        'open': 'first',
        'high': 'max',
        'low': 'min',
        'close': 'last'
    }).dropna()
    
    daily['range'] = daily['high'] - daily['low']
    
    # Prior Day Range
    daily['prev_range'] = daily['range'].shift(1)
    daily['prev_high'] = daily['high'].shift(1)
    daily['prev_low'] = daily['low'].shift(1)
    
    # 2 days ago
    daily['prev2_high'] = daily['high'].shift(2)
    daily['prev2_low'] = daily['low'].shift(2)
    
    # NR7: prev_range < min of ranges from shift(2) to shift(7)
    rolling_min_6 = daily['range'].shift(2).rolling(6).min()
    daily['is_nr7'] = daily['prev_range'] < rolling_min_6
    
    # Inside Day: prev_high <= prev2_high and prev_low >= prev2_low
    daily['is_inside_day'] = (daily['prev_high'] <= daily['prev2_high']) & (daily['prev_low'] >= daily['prev2_low'])
    
    daily.reset_index(inplace=True)
    daily['session_date'] = daily['time'].dt.strftime('%Y-%m-%d')
    return daily[['session_date', 'is_nr7', 'is_inside_day', 'prev_range']]

def run_orb_crabel_audit():
    df_trades = pd.read_csv(PROJECT_ROOT / 'storage/analysis/orb_nunez_2y/trades.csv')
    enabled_orb = ['Wall Street 30', 'XAUUSD', 'US Tech 100', 'BTCUSD']
    current = df_trades[(df_trades['variant'] == 'CURRENT') & (df_trades['symbol'].isin(enabled_orb))].copy()
    
    print(f"Total Enabled CURRENT trades: {len(current)}")
    
    # Merge with daily indicators
    enhanced_trades = []
    for sym in enabled_orb:
        sym_trades = current[current['symbol'] == sym].copy()
        daily = compute_daily_ranges(sym)
        if daily is not None:
            merged = pd.merge(sym_trades, daily, on='session_date', how='left')
            enhanced_trades.append(merged)
        else:
            sym_trades['is_nr7'] = False
            sym_trades['is_inside_day'] = False
            enhanced_trades.append(sym_trades)
            
    all_df = pd.concat(enhanced_trades).reset_index(drop=True)
    all_df['is_nr7'] = all_df['is_nr7'].fillna(False)
    all_df['is_inside_day'] = all_df['is_inside_day'].fillna(False)
    all_df['crabel_either'] = all_df['is_nr7'] | all_df['is_inside_day']
    all_df['crabel_both'] = all_df['is_nr7'] & all_df['is_inside_day']
    
    print("\n--- ABLATION RESULTS ON ENABLED ORB UNIVERSE (199 TRADES) ---")
    
    configs = [
        ("Base (Sin Filtros)", np.ones(len(all_df), dtype=bool)),
        ("NR7 Unicamente", all_df['is_nr7'].values),
        ("Inside Day Unicamente", all_df['is_inside_day'].values),
        ("NR7 O Inside Day (Either)", all_df['crabel_either'].values),
        ("NR7 Y Inside Day (Both)", all_df['crabel_both'].values),
    ]
    
    for name, mask in configs:
        sub = all_df[mask]
        n = len(sub)
        if n == 0:
            print(f"{name:30s}: 0 trades")
            continue
        net_r = sub['net_r'].sum()
        wr = (sub['net_r'] > 0).mean() * 100
        gross_w = sub[sub['net_r'] > 0]['net_r'].sum()
        gross_l = abs(sub[sub['net_r'] < 0]['net_r'].sum())
        pf = gross_w / gross_l if gross_l > 0 else float('inf')
        exp = net_r / n
        print(f"{name:30s}: N={n:3d} | Net R = {net_r:+6.2f} R | WR = {wr:5.1f}% | PF = {pf:5.3f} | Exp = {exp:+6.4f} R/t")
        
    print("\n--- DETALLE POR ACTIVO CON FILTRO CRABEL EITHER (NR7 O INSIDE DAY) ---")
    sub_crabel = all_df[all_df['crabel_either']]
    for sym in enabled_orb:
        sym_sub = sub_crabel[sub_crabel['symbol'] == sym]
        n = len(sym_sub)
        if n > 0:
            net_r = sym_sub['net_r'].sum()
            wr = (sym_sub['net_r'] > 0).mean() * 100
            print(f"  {sym:20s}: N={n:2d} | Net R = {net_r:+6.2f} R | WR = {wr:5.1f}%")

if __name__ == '__main__':
    run_orb_crabel_audit()
