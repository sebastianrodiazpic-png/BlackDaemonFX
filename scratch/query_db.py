import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from tools.operator.operator_db import get_readonly_connection, resolve_database_path

path = resolve_database_path()
print("Resolved path:", path)
conn = get_readonly_connection()
cur = conn.cursor()
cur.execute("SELECT COUNT(*) FROM daemon_audit_events;")
print("Total audit events:", cur.fetchone()[0])

query1 = """
SELECT DISTINCT instrument, action, reason 
FROM daemon_audit_events 
WHERE (reason LIKE '%KILLZONE%' OR reason LIKE '%ASIA%' OR reason LIKE '%STANDBY%' OR reason LIKE '%CLOSED%' OR reason LIKE '%SESSION%' OR action LIKE '%KILLZONE%' OR action LIKE '%STANDBY%');
"""
cur.execute(query1)
rows = cur.fetchall()
print("\nFilas con KILLZONE/ASIA/STANDBY/SESSION:")
for r in rows:
    print(dict(r))

query2 = """
SELECT created_at, instrument, action, reason 
FROM daemon_audit_events 
WHERE instrument LIKE '%Index%' OR instrument LIKE '%Volatility%' OR instrument LIKE '%Step%' OR instrument LIKE '%Boom%' OR instrument LIKE '%Crash%' OR instrument LIKE '%Jump%' 
ORDER BY id DESC LIMIT 30;
"""
cur.execute(query2)
synth_rows = cur.fetchall()
print("\nUltimos 30 eventos de sintéticos:")
for r in synth_rows:
    print(dict(r))

query3 = """
SELECT bot_profile, status, last_action, last_reason, updated_at 
FROM worker_runtime_states 
ORDER BY updated_at DESC;
"""
cur.execute(query3)
workers = cur.fetchall()
print("\nWorkers runtime states:")
for w in workers:
    print(dict(w))

conn.close()
