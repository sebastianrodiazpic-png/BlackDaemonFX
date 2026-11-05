import sqlite3

c = sqlite3.connect('file:C:/Users/sebas/AppData/Local/BlackDaemonFx/trading_bot.sqlite3?mode=ro', uri=True)
cur = c.cursor()
cur.execute("SELECT id, source, instrument, direction, entry_price, stop_loss, take_profit, status, result, net_pnl, created_at FROM trades ORDER BY id DESC LIMIT 5")
for r in cur.fetchall():
    print(r)
