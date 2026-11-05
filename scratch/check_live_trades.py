import sqlite3

c = sqlite3.connect('file:C:/Users/sebas/AppData/Local/BlackDaemonFx/trading_bot.sqlite3?mode=ro', uri=True)
cur = c.cursor()
cur.execute("SELECT COUNT(*) FROM trades WHERE status = 'OPEN'")
print('Open trades:', cur.fetchone()[0])
cur.execute("SELECT id, symbol, direction, entry_price, sl_price, tp1_price, created_at, status FROM trades ORDER BY id DESC LIMIT 5")
for r in cur.fetchall():
    print(r)
