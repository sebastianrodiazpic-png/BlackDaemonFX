import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import sqlite3
import json
import pandas as pd
from database.database import resolve_db_path

db_path = resolve_db_path()
conn = sqlite3.connect(f"file:{db_path.as_posix()}?mode=ro", uri=True)

print("=== MSNR CANDIDATES: STATES ===")
print(pd.read_sql_query("SELECT state, count(*) as count FROM msnr_candidates GROUP BY state", conn))

print("\n=== MSNR CANDIDATES: EXECUTED ===")
print(pd.read_sql_query("SELECT executed, count(*) as count FROM msnr_candidates GROUP BY executed", conn))

print("\n=== MSNR CANDIDATES: LAST REASONS ===")
print(pd.read_sql_query("SELECT state, last_reason, count(*) as count FROM msnr_candidates GROUP BY state, last_reason ORDER BY count DESC LIMIT 25", conn))

print("\n=== CANDIDATES EXECUTED == 1 (OR CONFIRMED) ===")
print(pd.read_sql_query("SELECT candidate_key, symbol, setup_id, state, first_seen, last_seen, confirmed_at, executed, last_reason FROM msnr_candidates WHERE executed = 1 OR confirmed_at IS NOT NULL OR state = 'CONFIRMED' LIMIT 20", conn))

print("\n=== RECENT CANDIDATES (FROM LAST 2 DAYS) ===")
print(pd.read_sql_query("SELECT candidate_key, symbol, setup_id, state, first_seen, last_seen, last_reason, executed FROM msnr_candidates ORDER BY last_seen DESC LIMIT 20", conn))

print("\n=== RUNTIME SETTINGS (ID 20) FOR MALAYSIAN_SNR ===")
cursor = conn.cursor()
row = cursor.execute("SELECT id, source, strategy_name, settings_json, updated_at FROM strategy_runtime_preferences WHERE id = 20").fetchone()
if row:
    s = json.loads(row[3])
    print(f"ID {row[0]}, Source {row[1]}, Strategy {row[2]}, Updated {row[4]}")
    for k, v in s.items():
        if any(w in k.lower() for w in ['ai', 'filter', 'min', 'max', 'enable', 'confir', 'risk', 'mode', 'session', 'timeframe']):
            print(f"  {k}: {v}")

print("\n=== MSNR TRADES IN TRADES TABLE ===")
df_t = pd.read_sql_query("""
    SELECT id, external_ticket, instrument, timeframe, direction, status, result, exit_reason, planned_rr, realized_rr, net_pnl, setup_reason, strategy_version, created_at 
    FROM trades 
    WHERE strategy_version LIKE '%msnr%'
    ORDER BY id DESC
""", conn)
print(f"Total MSNR trades: {len(df_t)}")
print(df_t.to_string())

conn.close()
