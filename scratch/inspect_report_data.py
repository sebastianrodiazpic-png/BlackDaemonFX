import sqlite3
import json
import os
from datetime import datetime, timezone, timedelta

db_path = r'C:\Users\sebas\AppData\Local\BlackDaemonFx\trading_bot.sqlite3'
con = sqlite3.connect(db_path)
cur = con.cursor()

tables = [t[0] for t in cur.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()]
print("Tables in DB:", tables)

print("\n--- TABLE ROW COUNTS ---")
for t in tables:
    try:
        cnt = cur.execute(f"SELECT count(*) FROM [{t}]").fetchone()[0]
        print(f"  {t}: {cnt} rows")
    except Exception as e:
        print(f"  {t}: error {e}")

print("\n--- RECENT DAEMON AUDIT EVENTS (last 15) ---")
if 'daemon_audit_events' in tables:
    rows = cur.execute("SELECT id, event_type, instrument, action, reason, created_at FROM daemon_audit_events ORDER BY id DESC LIMIT 15").fetchall()
    for r in rows:
        print(r)

print("\n--- RECENT TRADES (last 10) ---")
if 'trades' in tables:
    rows = cur.execute("SELECT id, broker_position_ticket, instrument, direction, status, result, entry_price, exit_price, stop_loss, take_profit, planned_rr, realized_rr, net_pnl, created_at FROM trades ORDER BY id DESC LIMIT 10").fetchall()
    for r in rows:
        print(r)

print("\n--- WORKER RUNTIME STATES ---")
if 'worker_runtime_states' in tables:
    rows = cur.execute("SELECT bot_profile, status, pid, current_symbol, last_action, last_reason, updated_at FROM worker_runtime_states").fetchall()
    for r in rows:
        print(r)

print("\n--- AI AND MSNR CANDIDATES (if any) ---")
candidate_tables = [t for t in tables if 'candidate' in t or 'ai' in t or 'model' in t or 'sentinel' in t]
print("Matching tables:", candidate_tables)
for ct in candidate_tables:
    sample = cur.execute(f"SELECT * FROM [{ct}] ORDER BY 1 DESC LIMIT 3").fetchall()
    print(f"Sample from {ct}:", sample)

con.close()
