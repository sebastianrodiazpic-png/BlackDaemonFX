import sqlite3
import json
from datetime import datetime, timezone

db_path = r'C:\Users\sebas\AppData\Local\BlackDaemonFx\trading_bot.sqlite3'
conn = sqlite3.connect(db_path)
c = conn.cursor()

flip_symbols = [
    'Crash Boom Flip 1000 Index',
    'Crash Boom Flip 500 Index',
    'Crash Boom Flip 300 Index',
    'Crash Boom Flip 150 Index'
]

# 1. Update instrument_selection_preferences
c.execute('SELECT id, source, selected_symbols_json, version FROM instrument_selection_preferences')
rows = c.fetchall()
for r in rows:
    rid, rsrc, rjson, rver = r
    symbols = json.loads(rjson)
    for fs in flip_symbols:
        if fs not in symbols:
            symbols.append(fs)
    symbols = sorted(list(set(symbols)))
    now = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S.%f')
    c.execute('UPDATE instrument_selection_preferences SET selected_symbols_json = ?, version = version + 1, updated_at = ? WHERE id = ?',
              (json.dumps(symbols), now, rid))
    print(f'Updated instrument_selection_preferences ID {rid} ({rsrc}): {len(symbols)} symbols')

# 2. Update instrument_selection_profile_preferences for SYNTHETICS
c.execute("SELECT id, source, selected_symbols_json, version FROM instrument_selection_profile_preferences WHERE selection_profile = 'SYNTHETICS'")
synth_rows = c.fetchall()
for r in synth_rows:
    rid, rsrc, rjson, rver = r
    symbols = json.loads(rjson)
    for fs in flip_symbols:
        if fs not in symbols:
            symbols.append(fs)
    symbols = sorted(list(set(symbols)))
    now = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S.%f')
    c.execute('UPDATE instrument_selection_profile_preferences SET selected_symbols_json = ?, version = version + 1, updated_at = ? WHERE id = ?',
              (json.dumps(symbols), now, rid))
    print(f'Updated SYNTHETICS profile ID {rid} ({rsrc}): {len(symbols)} symbols')

# 3. Insert or update FLIP profile in instrument_selection_profile_preferences
for src in ['DEMO', 'LIVE']:
    c.execute("SELECT id, version FROM instrument_selection_profile_preferences WHERE selection_profile = 'FLIP' AND source = ?", (src,))
    existing = c.fetchone()
    now = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S.%f')
    if existing:
        c.execute('UPDATE instrument_selection_profile_preferences SET selected_symbols_json = ?, version = version + 1, updated_at = ? WHERE id = ?',
                  (json.dumps(flip_symbols), now, existing[0]))
        print(f'Updated FLIP profile ({src})')
    else:
        c.execute('INSERT INTO instrument_selection_profile_preferences (source, selection_profile, selected_symbols_json, version, updated_at) VALUES (?, ?, ?, ?, ?)',
                  (src, 'FLIP', json.dumps(flip_symbols), 1, now))
        print(f'Inserted FLIP profile ({src})')

conn.commit()
conn.close()
print('Database updated successfully!')
