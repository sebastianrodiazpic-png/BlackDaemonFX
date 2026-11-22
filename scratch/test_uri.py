import sqlite3
import os
from pathlib import Path

path = Path(os.environ.get("LOCALAPPDATA", "")) / "BlackDaemonFx" / "trading_bot.sqlite3"
print("Path exists:", path.exists(), path)

# Usar URI correcto con /// o conexion normal con PRAGMA query_only
uri = f"file:///{path.as_posix()}?mode=ro"
print("URI:", uri)

conn = sqlite3.connect(uri, uri=True, timeout=3.0)
conn.row_factory = sqlite3.Row
cur = conn.cursor()
cur.execute("PRAGMA query_only = ON;")
cur.execute("SELECT COUNT(*) FROM daemon_audit_events;")
print("Count in daemon_audit_events:", cur.fetchone()[0])

cur.execute("""
SELECT bot_profile, status, last_action, last_reason, updated_at 
FROM worker_runtime_states 
ORDER BY updated_at DESC;
""")
for r in cur.fetchall():
    print(dict(r))

cur.execute("""
SELECT DISTINCT instrument, action, reason 
FROM daemon_audit_events 
WHERE (reason LIKE '%KILLZONE%' OR reason LIKE '%ASIA%' OR reason LIKE '%STANDBY%' OR reason LIKE '%CLOSED%' OR reason LIKE '%SESSION%' OR action LIKE '%KILLZONE%' OR action LIKE '%STANDBY%');
""")
for r in cur.fetchall():
    print("SESSION EVENT:", dict(r))

cur.execute("""
SELECT created_at, instrument, action, reason 
FROM daemon_audit_events 
WHERE instrument LIKE '%Index%' OR instrument LIKE '%Volatility%' OR instrument LIKE '%Step%' OR instrument LIKE '%Boom%' OR instrument LIKE '%Crash%' OR instrument LIKE '%Jump%' 
ORDER BY id DESC LIMIT 25;
""")
for r in cur.fetchall():
    print("SYNTH:", dict(r))

conn.close()
