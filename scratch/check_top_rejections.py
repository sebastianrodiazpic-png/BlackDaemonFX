import sqlite3
import pandas as pd

p = r"C:\Users\sebas\AppData\Local\BlackDaemonFx\trading_bot.sqlite3"
conn = sqlite3.connect(f"file:{p}?mode=ro", uri=True)

print("=== ÚLTIMOS 50,000 EVENTOS EN DAEMON_AUDIT_EVENTS ===")

cur = conn.cursor()
cur.execute("SELECT max(id) FROM daemon_audit_events")
max_id = cur.fetchone()[0] or 0
min_id = max_id - 50000

print(f"Rango de IDs: {min_id} a {max_id}")

df_actions = pd.read_sql_query(f"""
    SELECT action, count(*) as count 
    FROM daemon_audit_events 
    WHERE id >= {min_id} AND (action LIKE '%REJECT%' OR action LIKE '%VETO%' OR action LIKE '%LOCK%' OR action LIKE '%BLOCKED%' OR action LIKE '%WAITING%')
    GROUP BY action 
    ORDER BY count DESC LIMIT 20
""", conn)
print("\nTop acciones de filtrado/espera:")
print(df_actions.to_string())

df_reasons = pd.read_sql_query(f"""
    SELECT reason, count(*) as count 
    FROM daemon_audit_events 
    WHERE id >= {min_id} AND (action LIKE '%REJECT%' OR action LIKE '%VETO%' OR action LIKE '%BLOCKED%' OR action LIKE '%LOCK%')
    GROUP BY reason 
    ORDER BY count DESC LIMIT 20
""", conn)
print("\nTop razones de rechazo/bloqueo:")
print(df_reasons.to_string())

conn.close()
