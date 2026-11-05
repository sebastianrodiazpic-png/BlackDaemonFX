import sqlite3
import json

for p in ['storage/database.sqlite']:
    conn = sqlite3.connect(p)
    cur = conn.cursor()
    cur.execute("SELECT symbols_json FROM instrument_selection_profiles WHERE profile='SYNTHETICS' ORDER BY id DESC LIMIT 1")
    row = cur.fetchone()
    if row:
        syms = json.loads(row[0])
        print(p, 'SYNTHETICS count:', len(syms))
        for s in syms:
            if '550' in s or 'Boom' in s or 'Crash' in s:
                if '550' in s:
                    print('  ', s)
    conn.close()
