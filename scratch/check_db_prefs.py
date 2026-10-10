import sqlite3, os, json

p = os.path.expanduser("~/AppData/Local/BlackDaemonFx/trading_bot.sqlite3")
if not os.path.exists(p):
    print("Database does not exist:", p)
    exit(0)

con = sqlite3.connect(p)
cur = con.cursor()
tables = [r[0] for r in cur.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()]
print("Tables:", tables)

for t in tables:
    if "instrument" in t.lower() or "preference" in t.lower() or "profile" in t.lower():
        print("=== Table:", t, "===")
        rows = cur.execute(f"SELECT * FROM {t}").fetchall()
        for r in rows:
            print(r)
