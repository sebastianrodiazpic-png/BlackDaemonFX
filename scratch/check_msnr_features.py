import sqlite3
from pathlib import Path

db_path = Path("storage/runtime/shadow_research.sqlite3")
con = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
cur = con.cursor()

rows = cur.execute("SELECT id, timestamp, variant, symbol, features_json FROM shadow_signals WHERE strategy='MSNR';").fetchall()
for r in rows:
    print(r)

con.close()
