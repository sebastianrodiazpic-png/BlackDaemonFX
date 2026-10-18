import sqlite3
from pathlib import Path

p = Path.home() / 'AppData/Local/BlackDaemonFx/trading_bot.sqlite3'
conn = sqlite3.connect(f'file:{p}?mode=ro', uri=True)
cur = conn.cursor()

cur.execute('SELECT count(*) FROM signals')
print('Total signals in live DB:', cur.fetchone()[0])

cur.execute('SELECT count(*) FROM signals WHERE created_at >= "2026-10-15"')
print('Signals today (2026-10-15):', cur.fetchone()[0])

cur.execute('SELECT max(created_at) FROM signals')
print('Latest signal created_at:', cur.fetchone()[0])

cur.execute('SELECT count(*) FROM trades WHERE exit_time >= "2026-10-15"')
print('Trades closed today in live bot:', cur.fetchone()[0])

cur.execute('SELECT count(*) FROM trades WHERE exit_time IS NULL')
print('Open positions right now in live bot:', cur.fetchone()[0])

print("\n--- RECENT 5 SIGNALS ---")
cur.execute('SELECT id, created_at, instrument, direction, strategy_name FROM signals ORDER BY id DESC LIMIT 5')
for r in cur.fetchall():
    print(r)

conn.close()
