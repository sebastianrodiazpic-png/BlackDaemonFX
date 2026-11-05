import sqlite3

c = sqlite3.connect('file:C:/Users/sebas/AppData/Local/BlackDaemonFx/trading_bot.sqlite3?mode=ro', uri=True)
cur = c.cursor()
cur.execute("PRAGMA table_info(trades)")
print([r[1] for r in cur.fetchall()])
