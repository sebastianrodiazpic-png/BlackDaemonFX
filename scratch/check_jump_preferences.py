import sqlite3
import pandas as pd

p = r"C:\Users\sebas\AppData\Local\BlackDaemonFx\trading_bot.sqlite3"
conn = sqlite3.connect(f"file:{p}?mode=ro", uri=True)

print("--- INSTRUMENT PREFERENCES ---")
try:
    df_pref = pd.read_sql_query("SELECT * FROM instrument_selection_preferences WHERE symbol LIKE '%Jump%'", conn)
    print(df_pref.to_string())
except Exception as e:
    print("Error:", e)

print("\n--- ALL INSTRUMENT PREFERENCES (count) ---")
try:
    df_all_pref = pd.read_sql_query("SELECT enabled, count(*) FROM instrument_selection_preferences GROUP BY enabled", conn)
    print(df_all_pref.to_string())
except Exception as e:
    print("Error:", e)

print("\n--- WORKER RUNTIME STATES ---")
try:
    df_workers = pd.read_sql_query("SELECT * FROM worker_runtime_states", conn)
    print(df_workers.to_string())
except Exception as e:
    print("Error:", e)

print("\n--- SIGNALS FOR JUMP ---")
try:
    df_sig = pd.read_sql_query("SELECT id, created_at, instrument, strategy, action, status, reason FROM signals WHERE instrument LIKE '%Jump%' ORDER BY id DESC LIMIT 20", conn)
    print(df_sig.to_string())
except Exception as e:
    print("Error:", e)

conn.close()
