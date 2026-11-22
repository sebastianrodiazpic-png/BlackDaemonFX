import sqlite3, os
from pathlib import Path

db_path = Path(os.environ.get('LOCALAPPDATA', '')) / 'BlackDaemonFx' / 'trading_bot.sqlite3'
conn = sqlite3.connect(f"file:{db_path.as_posix()}?mode=ro", uri=True)
conn.row_factory = sqlite3.Row
cur = conn.cursor()

cur.execute("""
    SELECT reason, source, payload_json, COUNT(*) as cnt
    FROM daemon_audit_events
    WHERE instrument = 'Wall Street 30' AND action = 'REGIME_FILTER_BLOCKED'
    GROUP BY source
""")
for r in cur.fetchall():
    print("Source:", r['source'], "Count:", r['cnt'])

cur.execute("""
    SELECT payload_json
    FROM daemon_audit_events
    WHERE instrument = 'Wall Street 30' AND action = 'REGIME_FILTER_BLOCKED'
    ORDER BY id DESC LIMIT 2
""")
for r in cur.fetchall():
    print("Payload:", r['payload_json'])

conn.close()
