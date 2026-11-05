import sqlite3, json

conn = sqlite3.connect('storage/database.sqlite')
cur = conn.cursor()
cur.execute("SELECT selection_profile, selected_symbols_json FROM instrument_selection_profile_preferences")
for prof, sjson in cur.fetchall():
    syms = json.loads(sjson)
    print(f'{prof}: {len(syms)} symbols')
    for s in syms:
        if '550' in s:
            print('  ', s)
conn.close()
