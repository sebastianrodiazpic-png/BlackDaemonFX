import sqlite3

conn = sqlite3.connect("storage/trading_bot.sqlite3")
cur = conn.cursor()

for table in ["worker_runtime_states", "signals", "trades", "daemon_audit_events"]:
    print("=" * 60)
    print("Table:", table)
    cols = [c[1] for c in cur.execute(f"PRAGMA table_info({table})").fetchall()]
    print("Columns:", cols)
    rows = cur.execute(f"SELECT * FROM {table} ORDER BY rowid DESC LIMIT 10").fetchall()
    print(f"Count of rows in {table}:", cur.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0])
    for r in rows:
        print(dict(zip(cols, r)))

conn.close()
