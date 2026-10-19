import sqlite3
import pandas as pd

con = sqlite3.connect('file:storage/runtime/shadow_research.sqlite3?mode=ro', uri=True)
df = pd.read_sql_query("SELECT * FROM shadow_signals WHERE strategy='MSNR' AND final_action='ACCEPTED_EXECUTION'", con)
con.close()

print(f"Accepted MSNR signals in shadow_research.sqlite3 (N={len(df)}):")
for idx, r in df.iterrows():
    print(f"ID {r['id']:2d} | Time: {r['timestamp']} | Sym: {r['symbol']:18s} | Dir: {r['direction']:4s} | Entry: {r['entry_price']} | SL: {r['stop_loss']} | Outcome: {r['market_outcome']} | RR: {r['market_rr']}")

print("\nChecking all accepted signals across both strategies (ICT & MSNR):")
con = sqlite3.connect('file:storage/runtime/shadow_research.sqlite3?mode=ro', uri=True)
df_all = pd.read_sql_query("SELECT * FROM shadow_signals WHERE final_action='ACCEPTED_EXECUTION'", con)
con.close()
df_all['timestamp'] = pd.to_datetime(df_all['timestamp'])
df_all = df_all.sort_values('timestamp').reset_index(drop=True)
print(f"Total accepted prospective signals: {len(df_all)}")
print("Sample of first 10:")
print(df_all[['id', 'timestamp', 'strategy', 'symbol', 'direction', 'market_outcome', 'market_rr']].head(10))
