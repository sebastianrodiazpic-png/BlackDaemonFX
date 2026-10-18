import sqlite3
from pathlib import Path

db_path = Path("storage/runtime/shadow_research.sqlite3")
if not db_path.exists():
    print(f"Database {db_path} does not exist.")
    exit(0)

con = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
cur = con.cursor()
tables = cur.execute("SELECT name FROM sqlite_master WHERE type='table';").fetchall()
print("Tables in shadow_research.sqlite3:", tables)

for t in tables:
    t_name = t[0]
    count = cur.execute(f"SELECT COUNT(*) FROM {t_name};").fetchone()[0]
    cols = [c[1] for c in cur.execute(f"PRAGMA table_info({t_name});").fetchall()]
    print(f"\nTable: {t_name} (rows: {count})")
    print(f"Columns: {cols}")
    sample = cur.execute(f"SELECT * FROM {t_name} LIMIT 3;").fetchall()
    for row in sample:
        print("  Sample row:", row)

con.close()
