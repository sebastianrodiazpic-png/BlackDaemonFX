import sqlite3

uri = 'file:storage/runtime/shadow_research.sqlite3?mode=ro'
conn = sqlite3.connect(uri, uri=True)
cur = conn.cursor()
tables = [r[0] for r in cur.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()]
print('Tables in shadow_research.sqlite3:', tables)
for t in tables:
    count = cur.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
    print(f"  {t}: {count} rows")
    cur.execute(f"PRAGMA table_info({t})")
    cols = [r[1] for r in cur.fetchall()]
    print(f"    cols: {cols}")
