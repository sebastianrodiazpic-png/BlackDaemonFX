import sqlite3
import json

conn = sqlite3.connect(r'C:\Users\sebas\AppData\Local\BlackDaemonFx\trading_bot.sqlite3')
for r in conn.execute("SELECT id, instrument, details_json FROM trades WHERE status='OPEN'").fetchall():
    d = json.loads(r[2]) if r[2] else {}
    m = d.get('metadata', {})
    print(r[0], r[1], 'MFE:', m.get('max_favorable_excursion_rr'), 'MAE:', m.get('max_adverse_excursion_rr'))
