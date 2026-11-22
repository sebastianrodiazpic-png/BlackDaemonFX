import glob
import os

print("=== REVISANDO REINICIOS Y CICLOS FRESCOS EN LOGS ===")

key_logs = [
    "storage/logs/bots/ict.log",
    "storage/logs/bots/step.log",
    "storage/logs/bots/crash.log",
    "storage/logs/bots/indicesb_snr.log",
    "storage/logs/bots/volatility_1.log",
]

for p in key_logs:
    if not os.path.exists(p):
        continue
    with open(p, "r", encoding="utf-8", errors="ignore") as f:
        lines = f.readlines()
    
    # Check if warmup occurred in the file
    warmup_found = any("warmup" in l.lower() for l in lines[-200:])
    
    # Get last 15 lines
    print(f"\n--- ÚLTIMAS LÍNEAS DE {os.path.basename(p)} ({len(lines)} líneas) ---")
    for l in lines[-12:]:
        print("  " + l.strip()[:140])

print("\n=== REVISANDO ESTADOS DE WORKERS EN SQLITE ===")
import sqlite3
import pandas as pd

db_path = "storage/trading_bot.sqlite3"
try:
    conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    df_st = pd.read_sql_query("SELECT * FROM worker_runtime_states", conn)
    print(f"Filas en worker_runtime_states: {len(df_st)}")
    if len(df_st) > 0:
        print(df_st.tail(5)[["worker_name", "status", "last_heartbeat", "updated_at"]])
except Exception as e:
    print(f"Error leyendo worker_runtime_states: {e}")
