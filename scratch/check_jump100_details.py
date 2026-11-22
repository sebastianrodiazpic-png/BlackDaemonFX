import sqlite3
import pandas as pd
import json

p = r"C:\Users\sebas\AppData\Local\BlackDaemonFx\trading_bot.sqlite3"
conn = sqlite3.connect(f"file:{p}?mode=ro", uri=True)

df = pd.read_sql_query("SELECT id, event_time, source, event_type, instrument, action, reason FROM daemon_audit_events WHERE instrument = 'Jump 100 Index' OR payload_json LIKE '%Jump 100%' ORDER BY id DESC LIMIT 15", conn)
print("--- Jump 100 Events ---")
for idx, row in df.iterrows():
    print(f"[{row['id']}] {row['event_time']} | type: {row['event_type']} | action: {row['action']} | reason: {row['reason']}")

# Also look at payload of the top 3 events
cur = conn.cursor()
cur.execute("SELECT id, event_time, action, reason, payload_json FROM daemon_audit_events WHERE instrument = 'Jump 100 Index' OR payload_json LIKE '%Jump 100%' ORDER BY id DESC LIMIT 3")
for r in cur.fetchall():
    print(f"\n=== Event ID {r[0]} ({r[1]}) Action: {r[2]} Reason: {r[3]} ===")
    try:
        p_obj = json.loads(r[4])
        # print non-huge keys
        for k, v in p_obj.items():
            if k not in ['df', 'candles', 'series']:
                print(f"  {k}: {str(v)[:200]}")
    except Exception as e:
        print("  raw payload:", str(r[4])[:300])

conn.close()
