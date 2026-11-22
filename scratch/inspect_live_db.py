import sqlite3
import pandas as pd

p = r"C:\Users\sebas\AppData\Local\BlackDaemonFx\trading_bot.sqlite3"
conn = sqlite3.connect(f"file:{p}?mode=ro", uri=True)

print("Total trades in live DB:", pd.read_sql_query("SELECT count(id) FROM trades", conn).iloc[0,0])

df = pd.read_sql_query("SELECT instrument, count(id) as count FROM trades GROUP BY instrument ORDER BY count DESC LIMIT 30", conn)
print("\nTop 30 instruments by trade count:")
print(df.to_string())

df_jump = pd.read_sql_query("SELECT * FROM trades WHERE instrument LIKE '%Jump%'", conn)
print("\nJump trades count:", len(df_jump))
if len(df_jump) > 0:
    print(df_jump[['id', 'instrument', 'entry_time', 'direction', 'result', 'net_pnl', 'setup_reason']].to_string())

# Also check rejections or reasons why Jump was rejected
cur = conn.cursor()
cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = [r[0] for r in cur.fetchall()]
print("\nTables in DB:", tables)

if "daemon_audit_events" in tables:
    df_events = pd.read_sql_query("SELECT * FROM daemon_audit_events WHERE event_type LIKE '%jump%' OR details_json LIKE '%Jump%' ORDER BY id DESC LIMIT 10", conn)
    print("\nAudit events related to Jump:", len(df_events))
    if len(df_events) > 0:
        print(df_events.to_string())

if "worker_runtime_states" in tables:
    df_workers = pd.read_sql_query("SELECT * FROM worker_runtime_states", conn)
    print("\nWorker runtime states:")
    print(df_workers.to_string())

conn.close()
