import MetaTrader5 as mt5
import pandas as pd
from datetime import datetime, timezone

if mt5.initialize():
    rates_h1 = mt5.copy_rates_from_pos('XAUUSD', mt5.TIMEFRAME_H1, 0, 50)
    rates_h4 = mt5.copy_rates_from_pos('XAUUSD', mt5.TIMEFRAME_H4, 0, 50)
    
    df_h1 = pd.DataFrame(rates_h1)
    df_h1['time'] = pd.to_datetime(df_h1['time'], unit='s', utc=True)
    df_h1['ema50'] = df_h1['close'].ewm(span=50, adjust=False).mean()
    df_h1['ema200'] = df_h1['close'].ewm(span=200, adjust=False).mean()

    df_h4 = pd.DataFrame(rates_h4)
    df_h4['time'] = pd.to_datetime(df_h4['time'], unit='s', utc=True)
    df_h4['ema50'] = df_h4['close'].ewm(span=50, adjust=False).mean()
    df_h4['ema200'] = df_h4['close'].ewm(span=200, adjust=False).mean()

    cur_h1 = df_h1.iloc[-1]
    cur_h4 = df_h4.iloc[-1]

    print("XAUUSD Price:", cur_h1["close"])
    print(f"H1 close={cur_h1['close']}, ema50={cur_h1['ema50']:.2f}, ema200={cur_h1['ema200']:.2f}")
    print(f"H4 close={cur_h4['close']}, ema50={cur_h4['ema50']:.2f}, ema200={cur_h4['ema200']:.2f}")
    
    print("\nUltimas 8 velas H1:")
    for idx, r in df_h1.iloc[-8:].iterrows():
        trend_c = "BULL" if r["close"] >= r["open"] else "BEAR"
        print(f"{r['time']} | Open: {r['open']} | High: {r['high']} | Low: {r['low']} | Close: {r['close']} | {trend_c}")

    mt5.shutdown()
else:
    print("MT5 not initialized")
