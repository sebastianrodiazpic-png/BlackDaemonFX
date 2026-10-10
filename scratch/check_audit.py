import sqlite3, os

p = os.path.expanduser('~/AppData/Local/BlackDaemonFx/trading_bot.sqlite3')
con = sqlite3.connect(p)
cur = con.cursor()
for r in cur.execute('SELECT event_type, event_message, created_at FROM daemon_audit_events WHERE event_message LIKE "%MALAYSIAN%" ORDER BY id DESC LIMIT 10').fetchall():
    print(r)
