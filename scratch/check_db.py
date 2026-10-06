import sqlite3
import json

db_path = r"C:\Users\sebas\AppData\Local\BlackDaemonFx\trading_bot.sqlite3"
conn = sqlite3.connect(db_path)
cur = conn.cursor()

tables = [r[0] for r in cur.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall() if "instrument" in r[0]]
print("Instrument tables:", tables)

for t in tables:
    print(f"\n--- Table {t} ---")
    for c in cur.execute(f"PRAGMA table_info({t})").fetchall():
        print("  col:", c)
    rows = cur.execute(f"SELECT * FROM {t}").fetchall()
    print("  Total rows:", len(rows))
    for r in rows:
        print("   row:", r)

conn.close()
