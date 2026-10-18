import sqlite3
import json

conn = sqlite3.connect(r'C:\Users\sebas\AppData\Local\BlackDaemonFx\trading_bot.sqlite3')
cur = conn.cursor()

tables = [r[0] for r in cur.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()]
print("Tables:", tables)

for t in ['quarantine', 'symbol_quarantine', 'daemon_audit_events', 'worker_runtime_state']:
    if t in tables:
        count = cur.execute(f"SELECT count(*) FROM {t}").fetchone()[0]
        print(f"Table {t}: {count} rows")

if 'symbol_quarantine' in tables:
    for r in cur.execute("SELECT * FROM symbol_quarantine").fetchall():
        print("  QUARANTINE:", r)

# Check last 10 audit events with STRIKE
for r in cur.execute("SELECT id, event_type, created_at, instrument, action, reason FROM daemon_audit_events WHERE event_type LIKE '%STRIKE%' OR action LIKE '%STRIKE%' ORDER BY id DESC LIMIT 10").fetchall():
    print("  STRIKE EVENT:", r)
