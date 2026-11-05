import sqlite3

conn = sqlite3.connect('storage/trading_bot.sqlite3')
cur = conn.cursor()
try:
    cur.execute("SELECT event_type, instrument, action, reason, created_at FROM daemon_audit_events WHERE event_type LIKE '%HUMAN_CRITERIA%' OR action LIKE '%HUMAN_CRITERIA%' ORDER BY id DESC LIMIT 20")
    rows = cur.fetchall()
    print('Audit rows:', len(rows))
    for r in rows:
        print(r[0], '|', r[1], '|', r[2], '|', r[3], '|', r[4])
except Exception as e:
    print('Error:', e)
