import sqlite3
import pandas as pd
import json

p = r"C:\Users\sebas\AppData\Local\BlackDaemonFx\trading_bot.sqlite3"
conn = sqlite3.connect(f"file:{p}?mode=ro", uri=True)

# Schema of instrument_selection_preferences
cur = conn.cursor()
cur.execute("PRAGMA table_info(instrument_selection_preferences)")
print("Cols instrument_selection_preferences:", [r[1] for r in cur.fetchall()])

cur.execute("SELECT * FROM instrument_selection_preferences")
print("Rows instrument_selection_preferences:", cur.fetchall())

cur.execute("PRAGMA table_info(instrument_selection_profile_preferences)")
print("\nCols instrument_selection_profile_preferences:", [r[1] for r in cur.fetchall()])

cur.execute("SELECT * FROM instrument_selection_profile_preferences")
rows = cur.fetchall()
for r in rows:
    print("Profile Pref:", r)

# Check Worker JUMP runtime state
df_jump_worker = pd.read_sql_query("SELECT * FROM worker_runtime_states WHERE bot_profile = 'JUMP'", conn)
print("\nWorker JUMP state:")
if len(df_jump_worker) > 0:
    for col in df_jump_worker.columns:
        print(f"  {col}: {df_jump_worker.iloc[0][col]}")

conn.close()
