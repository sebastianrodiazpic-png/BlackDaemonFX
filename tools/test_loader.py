"""Prueba inicial del detector y simulador ICT Sabri Malle."""
import os
import glob
import pandas as pd
import numpy as np

SPREADS = {
    "AUDUSD": 0.00015,
    "EURUSD": 0.00012,
    "GBPUSD": 0.00018,
    "USDCAD": 0.00016,
    "USDCHF": 0.00015,
    "USDJPY": 0.015,
    "BTCUSD": 18.0,
    "US_Oil": 0.15,
    "US_SP_500": 0.35,
    "US_Tech_100": 0.90,
    "Wall_Street_30": 1.80,
    "XAGUSD": 0.05,
    "XAUUSD": 0.50,
    "Boom_1000_Index": 0.20,
    "Crash_1000_Index": 0.20,
    "Jump_50_Index": 0.50,
    "Step_Index": 0.10,
    "Volatility_75_Index": 25.0,
    "Volatility_100_Index": 1.5,
}

def load_symbol_data(symbol):
    # Check forex_historical first
    h1_path = f"data/forex_historical/{symbol}_H1.csv"
    m15_path = f"data/forex_historical/{symbol}_M15.csv"
    m5_path = f"data/forex_historical/{symbol}_M5.csv"
    
    if not os.path.exists(h1_path):
        h1_path = f"data/historical/{symbol}_H1.csv"
        m15_path = f"data/historical/{symbol}_M15.csv"
        m5_path = f"data/historical/{symbol}_M5.csv"
        
    if not os.path.exists(h1_path):
        return None, None
        
    df_h1 = pd.read_csv(h1_path)
    df_h1['time'] = pd.to_datetime(df_h1['time'], utc=True)
    df_h1 = df_h1.sort_values('time').reset_index(drop=True)
    
    df_ltf = None
    if os.path.exists(m15_path):
        df_ltf = pd.read_csv(m15_path)
        df_ltf['time'] = pd.to_datetime(df_ltf['time'], utc=True)
        df_ltf = df_ltf.sort_values('time').reset_index(drop=True)
    elif os.path.exists(m5_path):
        df_ltf = pd.read_csv(m5_path)
        df_ltf['time'] = pd.to_datetime(df_ltf['time'], utc=True)
        df_ltf = df_ltf.sort_values('time').reset_index(drop=True)
    else:
        df_ltf = df_h1
        
    return df_h1, df_ltf

print("Testing EURUSD and XAUUSD loader...")
h1, ltf = load_symbol_data("EURUSD")
print(f"EURUSD: H1={len(h1)}, LTF={len(ltf)}")
h1_g, ltf_g = load_symbol_data("XAUUSD")
print(f"XAUUSD: H1={len(h1_g)}, LTF={len(ltf_g)}")
