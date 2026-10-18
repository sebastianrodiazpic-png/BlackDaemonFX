import sqlite3
import pandas as pd
import json

def inspect_data():
    conn_prod = sqlite3.connect("file:trading_bot.sqlite3?mode=ro", uri=True)
    cur_p = conn_prod.cursor()
    cur_p.execute("SELECT name FROM sqlite_master WHERE type='table'")
    print("Tables in prod DB:", [r[0] for r in cur_p.fetchall()])
    conn_prod.close()

    conn_stg = sqlite3.connect("file:storage/runtime/shadow_research_staging.sqlite3?mode=ro", uri=True)
    df_stg = pd.read_sql_query("SELECT * FROM shadow_signals", conn_stg)
    conn_stg.close()

    print("\n--- STAGING BREAKDOWN BY STRATEGY & SYMBOL (ALL ROWS) ---")
    print(df_stg.groupby(["strategy", "symbol"]).size())

    cutoff = "2026-10-15T17:35:16.304722+00:00"
    df_prosp = df_stg[df_stg["timestamp"] >= cutoff]

    print("\n--- PROSPECTIVE STAGING BREAKDOWN (variant='base' for ICT, 'enabled_19_h4_fresh' for MSNR) ---")
    base_ict = df_prosp[(df_prosp["strategy"] == "ICT") & (df_prosp["variant"] == "base")]
    print("\nICT prospective events:")
    for _, r in base_ict.iterrows():
        print(f"ID {r['id']} | {r['timestamp']} | {r['symbol']} | {r['direction']} | {r['simulated_outcome']} | {r['simulated_rr']:+.2f}R")

    print("\nICT Per-Asset Aggregations:")
    for sym, grp in base_ict.groupby("symbol"):
        net_rr = grp["simulated_rr"].sum()
        wins = (grp["simulated_rr"] > 0).sum()
        losses = (grp["simulated_rr"] < 0).sum()
        print(f"Symbol: {sym:<16} | Trades: {len(grp)} | Wins: {wins} | Losses: {losses} | Net RR: {net_rr:+.2f}R | Profitable: {net_rr > 0}")

if __name__ == "__main__":
    inspect_data()
