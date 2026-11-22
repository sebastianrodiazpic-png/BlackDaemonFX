import sqlite3, os, json
from pathlib import Path

db_path = Path(os.environ.get('LOCALAPPDATA', '')) / 'BlackDaemonFx' / 'trading_bot.sqlite3'
conn = sqlite3.connect(f"file:{db_path.as_posix()}?mode=ro", uri=True)
conn.row_factory = sqlite3.Row
cur = conn.cursor()

cur.execute("SELECT id, source, selection_profile, version, updated_at, selected_symbols_json FROM instrument_selection_profile_preferences WHERE source='DEMO'")
for r in cur.fetchall():
    syms = json.loads(r['selected_symbols_json'])
    print(f"Profile: {r['selection_profile']} (v{r['version']}) -> {len(syms)} symbols: {syms}")

conn.close()
