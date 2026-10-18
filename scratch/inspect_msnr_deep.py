import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import sqlite3
import json
import pandas as pd
from database.database import resolve_db_path

db_path = resolve_db_path()
conn = sqlite3.connect(f"file:{db_path.as_posix()}?mode=ro", uri=True)
cursor = conn.cursor()

print("=== MSNR CANDIDATES: STATES & REASONS ===")
df_states = pd.read_sql_query("SELECT state, count(*) as count FROM msnr_candidates GROUP BY state", conn)
print(df_states)

print("\n=== MSNR CANDIDATES: EXECUTED COUNT ===")
df_exec = pd.read_sql_query("SELECT executed, count(*) as count FROM msnr_candidates GROUP BY executed", conn)
print(df_exec)

print("\n=== MSNR CANDIDATES: LAST REASONS (TOP 15) ===")
df_reasons = pd.read_sql_query("SELECT last_reason, count(*) as count FROM msnr_candidates GROUP BY last_reason ORDER BY count DESC LIMIT 15", conn)
print(df_reasons)

print("\n=== MSNR TRANSITIONS: REASONS (TOP 20) ===")
df_trans = pd.read_sql_query("SELECT state, reason, count(*) as count FROM msnr_candidate_transitions GROUP BY state, reason ORDER BY count DESC LIMIT 20", conn)
print(df_trans)

print("\n=== RECENT CANDIDATES (LAST 10) ===")
df_recent = pd.read_sql_query("SELECT candidate_key, symbol, setup_id, state, last_seen, last_reason, confirmed_at, executed FROM msnr_candidates ORDER BY last_seen DESC LIMIT 10", conn)
print(df_recent)

print("\n=== STRATEGY RUNTIME PREFERENCES (MALAYSIAN SNR) ===")
df_pref = pd.read_sql_query("SELECT id, source, strategy_name, settings_json, updated_at FROM strategy_runtime_preferences WHERE lower(strategy_name) LIKE '%snr%' OR lower(strategy_name) LIKE '%malaysian%'", conn)
for idx, row in df_pref.iterrows():
    print(f"ID {row['id']} | Source {row['source']} | Strategy {row['strategy_name']} | Updated {row['updated_at']}")
    try:
        s = json.loads(row['settings_json'])
        print("  Settings keys:", list(s.keys()))
        for k in ['ai_confirmation_required', 'ai_minimum_score', 'ai_model_path', 'enabled', 'active', 'min_score', 'timeframe', 'confirmation_timeout_bars']:
            if k in s:
                print(f"    {k}: {s[k]}")
    except Exception as e:
        print(f"  Error parsing json: {e}")

print("\n=== TRADES STRATEGY / SETUP BREAKDOWN ===")
df_trades_breakdown = pd.read_sql_query("""
    SELECT strategy_version, setup_reason, count(*) as cnt 
    FROM trades 
    GROUP BY strategy_version, setup_reason 
    ORDER BY cnt DESC LIMIT 20
""", conn)
print(df_trades_breakdown)

print("\n=== ANY TRADES WITH MSNR / SNR / MALAYSIAN ===")
df_trades_msnr = pd.read_sql_query("""
    SELECT id, external_ticket, instrument, timeframe, direction, status, result, setup_reason, strategy_version, details_json, created_at 
    FROM trades 
    WHERE lower(setup_reason) LIKE '%snr%' 
       OR lower(strategy_version) LIKE '%snr%' 
       OR lower(details_json) LIKE '%snr%' 
       OR lower(setup_reason) LIKE '%msnr%'
    LIMIT 10
""", conn)
print(f"Count of matching trades: {len(df_trades_msnr)}")
if len(df_trades_msnr) > 0:
    print(df_trades_msnr)

conn.close()
