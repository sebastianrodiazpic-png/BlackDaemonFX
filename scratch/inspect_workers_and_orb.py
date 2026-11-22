import sqlite3
import json

live_db = r"C:\Users\sebas\AppData\Local\BlackDaemonFx\trading_bot.sqlite3"
conn = sqlite3.connect(f"file:{live_db}?mode=ro", uri=True)
cur = conn.cursor()

print("=== WORKER RUNTIME STATES ===")
cur.execute("SELECT * FROM worker_runtime_states")
cols = [c[0] for c in cur.description]
for r in cur.fetchall():
    d = dict(zip(cols, r))
    print(d)

print("\n=== DAEMON AUDIT EVENTS (ultimos 20) ===")
cur.execute("SELECT * FROM daemon_audit_events ORDER BY id DESC LIMIT 20")
cols = [c[0] for c in cur.description]
for r in cur.fetchall():
    d = dict(zip(cols, r))
    print(f"[{d.get('created_at')}] Worker: {d.get('worker')} | Event: {d.get('event_type')} | Details: {str(d.get('details'))[:120]}")

print("\n=== STRATEGY RUNTIME PREFERENCES ===")
cur.execute("SELECT * FROM strategy_runtime_preferences")
cols = [c[0] for c in cur.description]
for r in cur.fetchall():
    d = dict(zip(cols, r))
    print(d)

print("\n=== SIGNALS (ultimas 10 de ORB) ===")
cur.execute("SELECT * FROM signals WHERE strategy_name LIKE '%ORB%' OR setup_type LIKE '%ORB%' ORDER BY id DESC LIMIT 10")
cols = [c[0] for c in cur.description]
for r in cur.fetchall():
    d = dict(zip(cols, r))
    print(f"[{d.get('timestamp') or d.get('created_at')}] {d.get('symbol')} | {d.get('strategy_name')} | {d.get('signal_type')} | {d.get('reasons') or d.get('details_json')}")

conn.close()
