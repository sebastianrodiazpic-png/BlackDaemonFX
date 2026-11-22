import sqlite3
import sys
sys.stdout.reconfigure(encoding='utf-8')

conn = sqlite3.connect('database/trading_bot.sqlite3')
cur = conn.cursor()

for table in ['trades', 'signals', 'daily_profit_target_preferences', 'worker_runtime_states', 'strategy_runtime_preferences', 'daemon_audit_events']:
    print(f"\n=== SCHEMA FOR {table} ===")
    cur.execute(f"PRAGMA table_info({table})")
    cols = [f"{c[1]} ({c[2]})" for c in cur.fetchall()]
    print(", ".join(cols))
    
    print(f"--- RECENT 5 ROWS FOR {table} ---")
    cur.execute(f"SELECT * FROM {table} ORDER BY rowid DESC LIMIT 5")
    for row in cur.fetchall():
        print(row)
