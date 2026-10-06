import os
import time
from datetime import datetime, timezone
import pandas as pd
import MetaTrader5 as mt5

def download_symbol(sym, tf, tf_name, max_bars=120000, chunk_size=20000):
    mt5.symbol_select(sym, True)
    all_chunks = []
    for pos in range(0, max_bars, chunk_size):
        r = mt5.copy_rates_from_pos(sym, tf, pos, chunk_size)
        if r is None or len(r) == 0:
            break
        df = pd.DataFrame(r)
        df['time'] = pd.to_datetime(df['time'], unit='s', utc=True)
        all_chunks.append(df)
        print(f"  [{sym} {tf_name}] pos {pos}: fetched {len(df)} bars ({df['time'].iloc[0]} to {df['time'].iloc[-1]})", flush=True)
        if len(df) < chunk_size:
            break
        time.sleep(0.1)

    if not all_chunks:
        print(f"  [{sym} {tf_name}] No data found!", flush=True)
        return None

    full_df = pd.concat(all_chunks).drop_duplicates('time').sort_values('time').reset_index(drop=True)
    out_dir = "data/historical"
    os.makedirs(out_dir, exist_ok=True)
    clean_sym = sym.replace(" ", "_")
    csv_path = os.path.join(out_dir, f"{clean_sym}_{tf_name}.csv")
    full_df.to_csv(csv_path, index=False)
    print(f"-> Saved {len(full_df)} bars to {csv_path} ({full_df['time'].iloc[0]} to {full_df['time'].iloc[-1]})", flush=True)
    return full_df

def main():
    if not mt5.initialize():
        print("Failed to initialize MT5")
        return

    symbols = [
        "XAUUSD",
        "Wall Street 30",
        "US Tech 100",
        "BTCUSD",
        "US Oil",
        "US SP 500",
        "XAGUSD"
    ]

    summary = []
    for sym in symbols:
        info = mt5.symbol_info(sym)
        spread_price = info.spread * info.point if info else 0.0
        print(f"\nProcessing {sym} (Spread: {spread_price:.4f})...", flush=True)
        
        # M5
        df_m5 = download_symbol(sym, mt5.TIMEFRAME_M5, "M5", max_bars=150000, chunk_size=25000)
        # H1
        df_h1 = download_symbol(sym, mt5.TIMEFRAME_H1, "H1", max_bars=35000, chunk_size=20000)

        summary.append({
            "symbol": sym,
            "spread": spread_price,
            "m5_bars": len(df_m5) if df_m5 is not None else 0,
            "m5_start": str(df_m5['time'].iloc[0]) if df_m5 is not None else None,
            "m5_end": str(df_m5['time'].iloc[-1]) if df_m5 is not None else None,
            "h1_bars": len(df_h1) if df_h1 is not None else 0,
            "h1_start": str(df_h1['time'].iloc[0]) if df_h1 is not None else None,
            "h1_end": str(df_h1['time'].iloc[-1]) if df_h1 is not None else None,
        })

    mt5.shutdown()
    sum_df = pd.DataFrame(summary)
    sum_df.to_csv("data/historical/download_summary.csv", index=False)
    print("\n=== DOWNLOAD COMPLETE ===")
    print(sum_df.to_string())

if __name__ == "__main__":
    main()
