import sqlite3

conn = sqlite3.connect("file:database/trading_bot.sqlite3?mode=ro", uri=True)
cur = conn.cursor()
for table in ['trades', 'trade_journal']:
    cur.execute(f"PRAGMA table_info({table});")
    cols = cur.fetchall()
    print(f"=== {table} columns ===")
    for c in cols:
        print(f"  {c[1]} ({c[2]})")
conn.close()
