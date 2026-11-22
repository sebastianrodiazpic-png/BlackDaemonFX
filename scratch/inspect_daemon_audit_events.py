import sqlite3, json

for db_path in ["database/trading_bot.sqlite3", "storage/trading_bot.sqlite3"]:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    print(f"=== {db_path} daemon_audit_events ===")
    c.execute("SELECT * FROM daemon_audit_events ORDER BY rowid DESC LIMIT 20")
    rows = c.fetchall()
    print(f"Found {len(rows)} events:")
    for r in rows:
        d = dict(r)
        payload = d.get('payload_json')
        print(f"  [{d.get('event_time')}] {d.get('event_type')} | {d.get('instrument')} | action={d.get('action')} | reason={d.get('reason')}")
    conn.close()
