import sys, os
sys.path.insert(0, os.path.abspath("."))
import sqlite3, json
from database.database import resolve_db_path

c = sqlite3.connect(resolve_db_path()).cursor()

rows = c.execute("""
    SELECT id, cycle_number, payload_json, event_time
    FROM daemon_audit_events
    WHERE event_type='DAEMON_CYCLE_START' AND payload_json LIKE '%MALAYSIAN_SNR%'
    ORDER BY id DESC LIMIT 5
""").fetchall()

for r in rows:
    payload = json.loads(r[2]) if r[2] else {}
    print(f"Cycle Start {r[0]}, cycle={r[1]}, time={r[3]}: payload={payload}")
