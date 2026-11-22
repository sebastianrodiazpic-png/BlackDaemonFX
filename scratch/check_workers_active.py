import sqlite3
import pandas as pd

p = r"C:\Users\sebas\AppData\Local\BlackDaemonFx\trading_bot.sqlite3"
conn = sqlite3.connect(f"file:{p}?mode=ro", uri=True)

df_workers = pd.read_sql_query("SELECT id, bot_profile, daemon_magic, status, symbols_total, symbols_processed, current_symbol, last_action, last_reason, updated_at FROM worker_runtime_states WHERE source='DEMO'", conn)
print("=== ESTADO DE TODOS LOS WORKERS EN VIVO ===")
print(df_workers.to_string())

conn.close()
