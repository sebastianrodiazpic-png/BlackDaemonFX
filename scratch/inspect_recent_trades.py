import sqlite3
import os

db = os.path.expanduser('~') + r'\AppData\Local\BlackDaemonFx\trading_bot.sqlite3'
conn = sqlite3.connect(db)
c = conn.cursor()
rows = c.execute('''
    SELECT id, instrument, status, result, entry_time, exit_time, exit_reason, net_pnl 
    FROM trades 
    WHERE instrument = 'Step Index 500' 
    ORDER BY id DESC LIMIT 10
''').fetchall()
for r in rows:
    print(r)
