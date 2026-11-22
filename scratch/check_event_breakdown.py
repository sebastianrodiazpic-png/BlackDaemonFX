import sqlite3
import json

p = r"C:\Users\sebas\AppData\Local\BlackDaemonFx\trading_bot.sqlite3"
conn = sqlite3.connect(f"file:{p}?mode=ro", uri=True)

cur = conn.cursor()
cur.execute("SELECT id, event_time, payload_json FROM daemon_audit_events WHERE id IN (7187915, 7187917)")
for r in cur.fetchall():
    print(f"=== Event {r[0]} ({r[1]}) ===")
    obj = json.loads(r[2])
    print(json.dumps(obj, indent=2))

conn.close()
