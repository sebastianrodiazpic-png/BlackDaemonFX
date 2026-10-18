import sqlite3
import os

db = os.path.expanduser('~') + r'\AppData\Local\BlackDaemonFx\trading_bot.sqlite3'
conn = sqlite3.connect(db)
c = conn.cursor()
tables = c.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
for t in tables:
    name = t[0]
    count = c.execute(f"SELECT count(*) FROM [{name}]").fetchone()[0]
    print(f"{name}: {count}")
