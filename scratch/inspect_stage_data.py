import sqlite3
import json

db_path = r"C:\Users\sebas\AppData\Local\BlackDaemonFx\trading_bot.sqlite3"
conn = sqlite3.connect(db_path)
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

cursor.execute("""
    SELECT created_at, instrument, action, reason, payload_json
    FROM daemon_audit_events
    WHERE (payload_json LIKE '%MALAYSIAN_SNR%' OR action LIKE '%MALAYSIAN%')
      AND event_type = 'SYMBOL_PROCESS_RESULT'
      AND instrument = 'Step Index 400'
    ORDER BY id DESC LIMIT 1
""")
row = cursor.fetchone()
if row:
    pl = json.loads(row['payload_json'])
    res = pl.get('result', {})
    print("Step Index 400 stage_data:")
    print(json.dumps(res.get('stage_data'), indent=2))
    print("shadow_plan:")
    print(json.dumps(res.get('shadow_plan'), indent=2))

conn.close()
