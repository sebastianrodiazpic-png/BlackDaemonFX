import sqlite3
import json

conn = sqlite3.connect(r"file:C:\Users\sebas\AppData\Local\BlackDaemonFx\trading_bot.sqlite3?mode=ro", uri=True)
conn.row_factory = sqlite3.Row
cur = conn.cursor()

print("--- worker_runtime_states columns ---")
print([c[1] for c in cur.execute("PRAGMA table_info(worker_runtime_states)").fetchall()])
w_rows = cur.execute("SELECT * FROM worker_runtime_states").fetchall()
for r in w_rows:
    d = dict(r)
    # print essential fields
    print(f"Worker {d.get('worker_name') or d.get('profile') or d.get('id')}: status={d.get('status')} state={d.get('state')} pid={d.get('pid')} updated={d.get('updated_at') or d.get('last_heartbeat')}")

print("\n--- signals columns ---")
print([c[1] for c in cur.execute("PRAGMA table_info(signals)").fetchall()])
s_rows = cur.execute("SELECT * FROM signals ORDER BY id DESC LIMIT 10").fetchall()
for s in s_rows:
    d = dict(s)
    print(f"Signal {d.get('id')}: {d.get('instrument')} {d.get('signal_type') or d.get('direction')} status={d.get('status')} reason={d.get('reason') or d.get('rejection_reason')}")

print("\n--- trade_journal columns ---")
print([c[1] for c in cur.execute("PRAGMA table_info(trade_journal)").fetchall()])
j_rows = cur.execute("SELECT * FROM trade_journal ORDER BY id DESC LIMIT 10").fetchall()
for j in j_rows:
    d = dict(j)
    print(f"Journal {d.get('id')} (trade {d.get('trade_id')}): stage={d.get('stage') or d.get('event')} note={str(d.get('notes') or d.get('note') or d.get('message'))[:80]}")
