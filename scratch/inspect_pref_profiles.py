import sqlite3
import pandas as pd
import json

p = r"C:\Users\sebas\AppData\Local\BlackDaemonFx\trading_bot.sqlite3"
conn = sqlite3.connect(f"file:{p}?mode=ro", uri=True)

df = pd.read_sql_query("SELECT id, source, selection_profile, selected_symbols_json, updated_at FROM instrument_selection_profile_preferences", conn)
print("=== PERFILES ACTUALES EN SQLITE ===")
for _, r in df.iterrows():
    syms = json.loads(r['selected_symbols_json'])
    print(f"[{r['id']}] {r['source']} | {r['selection_profile']} | {len(syms)} symbols: {syms[:5]}...")

conn.close()
