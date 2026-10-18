import sqlite3, json

conn = sqlite3.connect(r'C:\Users\sebas\AppData\Local\BlackDaemonFx\trading_bot.sqlite3')
rows = conn.execute("SELECT id, bot_profile, status, current_symbol, last_action, last_reason, updated_at FROM worker_runtime_states ORDER BY id").fetchall()
print(f"{'PROFILE':<16} | {'STATUS':<20} | {'SYMBOL':<22} | {'ACTION':<24} | {'LAST REASON'}")
print("-" * 110)
for r in rows:
    print(f"{r[1]:<16} | {r[2]:<20} | {str(r[3]):<22} | {str(r[4]):<24} | {str(r[5])[:45]}")
