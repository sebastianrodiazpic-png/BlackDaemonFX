import sqlite3
import json
import pandas as pd

db_path = r'C:/Users/sebas/AppData/Local/BlackDaemonFx/trading_bot.sqlite3'
conn = sqlite3.connect(f'file:{db_path}?mode=ro', uri=True)

query = """
SELECT id, event_time, instrument, action, reason, payload_json
FROM daemon_audit_events
WHERE event_type = 'HUMAN_CRITERIA_EVALUATED'
ORDER BY id DESC
LIMIT 50
"""
df = pd.read_sql_query(query, conn)
print(f"Total rows inspected: {len(df)}")
for idx, r in df.head(20).iterrows():
    p = json.loads(r['payload_json']) if r['payload_json'] else {}
    print(f"ID {r['id']} | {r['instrument']} | {r['action']} | {r['reason']}")
    print(f"   Score: {p.get('score')} | Grade: {p.get('grade')} | Breakdown: {p.get('breakdown')}")
