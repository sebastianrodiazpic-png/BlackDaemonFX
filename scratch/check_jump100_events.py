import sqlite3
import pandas as pd

p = r"C:\Users\sebas\AppData\Local\BlackDaemonFx\trading_bot.sqlite3"
conn = sqlite3.connect(f"file:{p}?mode=ro", uri=True)

cur = conn.cursor()
cur.execute("PRAGMA table_info(daemon_audit_events)")
cols = [r[1] for r in cur.fetchall()]
print("daemon_audit_events cols:", cols)

q = "SELECT * FROM daemon_audit_events WHERE "
conditions = []
for c in cols:
    conditions.append(f"{c} LIKE '%Jump 100%'")
q += " OR ".join(conditions) + " ORDER BY id DESC LIMIT 20"

try:
    df = pd.read_sql_query(q, conn)
    print("Found events for Jump 100:", len(df))
    if len(df) > 0:
        print(df.to_string())
except Exception as e:
    print("Error querying events:", e)

# Also check signals table
cur.execute("PRAGMA table_info(signals)")
sig_cols = [r[1] for r in cur.fetchall()]
print("\nsignals cols:", sig_cols)

q_sig = "SELECT * FROM signals WHERE "
sig_conds = []
for c in sig_cols:
    sig_conds.append(f"{c} LIKE '%Jump 100%'")
q_sig += " OR ".join(sig_conds) + " ORDER BY id DESC LIMIT 20"

try:
    df_sig = pd.read_sql_query(q_sig, conn)
    print("Found signals for Jump 100:", len(df_sig))
    if len(df_sig) > 0:
        print(df_sig.to_string())
except Exception as e:
    print("Error querying signals:", e)

conn.close()
