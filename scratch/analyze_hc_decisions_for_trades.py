import sqlite3
import json
import pandas as pd

db_path = r'C:/Users/sebas/AppData/Local/BlackDaemonFx/trading_bot.sqlite3'
conn = sqlite3.connect(f'file:{db_path}?mode=ro', uri=True)

print("=== HUMAN CRITERIA AUDIT ACTIONS COUNT ===")
q_acts = """
SELECT action, count(*), min(created_at), max(created_at)
FROM daemon_audit_events
WHERE event_type = 'HUMAN_CRITERIA_EVALUATED'
GROUP BY action
"""
print(pd.read_sql_query(q_acts, conn).to_string())

print("\n=== SAMPLE HUMAN CRITERIA PASSED EVENTS ===")
q_passed = """
SELECT instrument, action, reason, payload_json, created_at
FROM daemon_audit_events
WHERE event_type = 'HUMAN_CRITERIA_EVALUATED' AND action = 'HUMAN_CRITERIA_PASSED'
ORDER BY id DESC
LIMIT 15
"""
df_p = pd.read_sql_query(q_passed, conn)
for idx, row in df_p.iterrows():
    print(f"\n{row['created_at']} | {row['instrument']} | Action: {row['action']} | Reason: {row['reason']}")
    print(f"   Payload: {row['payload_json']}")

print("\n=== SAMPLE HUMAN CRITERIA VETOED EVENTS ===")
q_vetoed = """
SELECT instrument, action, reason, payload_json, created_at
FROM daemon_audit_events
WHERE event_type = 'HUMAN_CRITERIA_EVALUATED' AND action != 'HUMAN_CRITERIA_PASSED'
ORDER BY id DESC
LIMIT 15
"""
df_v = pd.read_sql_query(q_vetoed, conn)
for idx, row in df_v.iterrows():
    print(f"\n{row['created_at']} | {row['instrument']} | Action: {row['action']} | Reason: {row['reason']}")
    print(f"   Payload: {row['payload_json']}")
