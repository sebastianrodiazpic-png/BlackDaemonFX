import sqlite3
import json

db_path = r'C:/Users/sebas/AppData/Local/BlackDaemonFx/trading_bot.sqlite3'
conn = sqlite3.connect(f'file:{db_path}?mode=ro', uri=True)
cur = conn.cursor()

print("=== CHECK DETAILS_JSON KEYS FOR RECENT TRADES ===")
cur.execute("SELECT id, instrument, setup_reason, details_json FROM trades ORDER BY id DESC LIMIT 5")
for tid, inst, setup_r, d_json in cur.fetchall():
    d = json.loads(d_json) if d_json else {}
    print(f"\nTrade ID {tid} ({inst}):")
    print("Top-level keys in details_json:", list(d.keys()))
    if 'human_criteria' in d:
        print("  Found human_criteria in d:", d['human_criteria'])
    meta = d.get('metadata') or {}
    print("Metadata keys:", list(meta.keys()))
    if 'human_criteria' in meta:
        print("  Found human_criteria in metadata:", meta['human_criteria'])

print("\n=== CHECK DAEMON_AUDIT_EVENTS FOR HUMAN_CRITERIA ===")
cur.execute("SELECT count(*) FROM daemon_audit_events WHERE event_type LIKE '%HUMAN%'")
print("Total HUMAN_CRITERIA events in audit:", cur.fetchone()[0])

cur.execute("SELECT event_type, instrument, action, reason, created_at FROM daemon_audit_events WHERE event_type LIKE '%HUMAN%' ORDER BY id DESC LIMIT 10")
for r in cur.fetchall():
    print(" ", r)
