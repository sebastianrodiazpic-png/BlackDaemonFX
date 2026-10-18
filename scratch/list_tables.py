import sqlite3

conn = sqlite3.connect(r"file:C:\Users\sebas\AppData\Local\BlackDaemonFx\trading_bot.sqlite3?mode=ro", uri=True)
tables = [r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()]
print("Tables in SQLite database:")
for t in sorted(tables):
    count = conn.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
    print(f"  - {t} ({count} rows)")
