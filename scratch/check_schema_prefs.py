import sqlite3, os
from pathlib import Path

db_path = Path(os.environ.get('LOCALAPPDATA', '')) / 'BlackDaemonFx' / 'trading_bot.sqlite3'
conn = sqlite3.connect(f"file:{db_path.as_posix()}?mode=ro", uri=True)
conn.row_factory = sqlite3.Row
cur = conn.cursor()

cur.execute("PRAGMA table_info('instrument_selection_profile_preferences')")
for r in cur.fetchall():
    print(dict(r))

cur.execute("SELECT * FROM instrument_selection_profile_preferences LIMIT 5")
for r in cur.fetchall():
    d = dict(r)
    d['selected_symbols_json'] = f"len={len(d.get('selected_symbols_json', ''))}"
    print(d)

conn.close()
