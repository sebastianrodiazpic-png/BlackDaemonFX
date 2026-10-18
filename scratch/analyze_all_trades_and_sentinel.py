import sqlite3
import json

db_path = r"C:\Users\sebas\AppData\Local\BlackDaemonFx\trading_bot.sqlite3"
conn = sqlite3.connect(db_path)
conn.row_factory = sqlite3.Row
cur = conn.cursor()

tables = [t[0] for t in cur.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()]
print("Tables in DB:", tables)

print("\n--- RECENT DAEMON AUDIT EVENTS ---")
recent_events = cur.execute("SELECT id, event_type, created_at FROM daemon_audit_events ORDER BY id DESC LIMIT 20").fetchall()
for e in recent_events:
    print(f"ID {e['id']} | {e['event_type']} | {e['created_at']}")

# Let's inspect sentinel / regime tables or events if any
sentinel_events = cur.execute("SELECT id, event_type, payload_json, created_at FROM daemon_audit_events WHERE event_type LIKE '%sentinel%' OR event_type LIKE '%regime%' ORDER BY id DESC LIMIT 10").fetchall()
print(f"\nSentinel/Regime Events ({len(sentinel_events)}):")
for se in sentinel_events:
    print(f"ID {se['id']} | {se['event_type']} | {se['created_at']} | {se['payload_json'][:150]}")

# Let's inspect signal analysis rejections
rejections = cur.execute("SELECT id, event_type, payload_json, created_at FROM daemon_audit_events WHERE event_type LIKE '%REJECT%' OR event_type LIKE '%FILTER%' OR event_type LIKE '%SKIP%' ORDER BY id DESC LIMIT 10").fetchall()
print(f"\nRecent Signal Rejection/Filter Events ({len(rejections)}):")
for r in rejections:
    print(f"ID {r['id']} | {r['event_type']} | {r['created_at']} | {r['payload_json'][:150]}")
