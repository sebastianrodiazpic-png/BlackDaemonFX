import sqlite3, json

conn = sqlite3.connect(r'C:\Users\sebas\AppData\Local\BlackDaemonFx\trading_bot.sqlite3')
rows = conn.execute("SELECT bot_profile, status, last_reason, updated_at FROM worker_runtime_states").fetchall()
for r in rows:
    print(r)
