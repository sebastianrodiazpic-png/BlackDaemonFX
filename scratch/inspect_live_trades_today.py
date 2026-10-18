import sqlite3
from pathlib import Path

p = Path.home() / 'AppData/Local/BlackDaemonFx/trading_bot.sqlite3'
conn = sqlite3.connect(f'file:{p}?mode=ro', uri=True)
conn.row_factory = sqlite3.Row
cur = conn.cursor()

cur.execute('PRAGMA table_info(trades)')
cols = [r['name'] for r in cur.fetchall()]
print('Trades cols:', cols)

cur.execute('SELECT * FROM trades WHERE entry_time >= "2026-10-15" OR exit_time >= "2026-10-15" ORDER BY id DESC LIMIT 20')
rows = cur.fetchall()
print(f'Found {len(rows)} trades today in live bot.')
for r in rows:
    d = dict(r)
    print({
        'id': d.get('id'),
        'external_ticket': d.get('external_ticket'),
        'instrument': d.get('instrument'),
        'direction': d.get('direction'),
        'status': d.get('status'),
        'result': d.get('result'),
        'entry_time': d.get('entry_time'),
        'exit_time': d.get('exit_time'),
        'entry_price': d.get('entry_price'),
        'exit_price': d.get('exit_price'),
        'realized_rr': d.get('realized_rr'),
        'net_pnl': d.get('net_pnl'),
        'exit_reason': d.get('exit_reason'),
        'setup_reason': d.get('setup_reason')
    })
conn.close()
