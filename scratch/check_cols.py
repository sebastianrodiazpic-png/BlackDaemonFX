import sqlite3

db_path = r'C:/Users/sebas/AppData/Local/BlackDaemonFx/trading_bot.sqlite3'
conn = sqlite3.connect(f'file:{db_path}?mode=ro', uri=True)
cur = conn.cursor()

print("=== TRADES COLUMNS ===")
cur.execute("PRAGMA table_info(trades)")
cols = [r[1] for r in cur.fetchall()]
print(cols)

print("\n=== TRADE_JOURNAL COLUMNS ===")
cur.execute("PRAGMA table_info(trade_journal)")
jcols = [r[1] for r in cur.fetchall()]
print(jcols)

print("\n=== SAMPLE 3 ROWS FROM TRADES ===")
cur.execute(f"SELECT * FROM trades ORDER BY id DESC LIMIT 3")
rows = cur.fetchall()
for r in rows:
    print(dict(zip(cols, r)))

print("\n=== SAMPLE 3 ROWS FROM TRADE_JOURNAL ===")
cur.execute(f"SELECT * FROM trade_journal ORDER BY id DESC LIMIT 3")
jrows = cur.fetchall()
for r in jrows:
    print(dict(zip(jcols, r)))
