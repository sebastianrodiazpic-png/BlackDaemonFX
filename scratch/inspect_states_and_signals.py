import sqlite3
import json

conn = sqlite3.connect(r"file:C:\Users\sebas\AppData\Local\BlackDaemonFx\trading_bot.sqlite3?mode=ro", uri=True)
conn.row_factory = sqlite3.Row
cur = conn.cursor()

for tbl in ["worker_runtime_states", "signals", "trade_journal"]:
    cols = [c[1] for c in cur.execute(f"PRAGMA table_info({tbl})").fetchall()]
    print(f"Schema {tbl}: {cols}")
    rows = cur.execute(f"SELECT * FROM {tbl} ORDER BY rowid DESC LIMIT 5").fetchall()
    print(f"Sample row from {tbl}:")
    for r in rows[:1]:
        print(f"  {dict(r)}")
    print("-" * 50)

