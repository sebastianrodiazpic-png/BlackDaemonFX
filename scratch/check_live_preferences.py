import sqlite3, os, json
from pathlib import Path

db_path = Path(os.environ.get('LOCALAPPDATA', '')) / 'BlackDaemonFx' / 'trading_bot.sqlite3'
conn = sqlite3.connect(f"file:{db_path.as_posix()}?mode=ro", uri=True)
conn.row_factory = sqlite3.Row
cur = conn.cursor()

print("================ LIVE DB: instrument_selection_profile_preferences ================")
cur.execute("SELECT id, source, profile, updated_at, LENGTH(selected_symbols_json) as len_json FROM instrument_selection_profile_preferences")
rows = cur.fetchall()
for r in rows:
    print(f"ID #{r['id']} | src={r['source']} | profile={r['profile']} | updated={r['updated_at']} | json_len={r['len_json']}")

print("\nSample for profile ICT and MALAYSIAN_SNR:")
cur.execute("SELECT profile, selected_symbols_json FROM instrument_selection_profile_preferences WHERE profile IN ('ICT', 'MALAYSIAN_SNR', 'INDICESB_SNR')")
for r in cur.fetchall():
    syms = json.loads(r['selected_symbols_json'])
    print(f"Profile: {r['profile']} ({len(syms)} symbols)")
    print(f"   Symbols: {syms[:10]} ... {syms[-5:]}")

conn.close()
