import sqlite3

db_path = 'database/trading_bot.sqlite3'
conn = sqlite3.connect(db_path)

print("--- instrument_selection_profile_preferences ---")
for r in conn.execute("SELECT * FROM instrument_selection_profile_preferences").fetchall():
    print(" ", r)

print("\n--- daemon_audit_events ---")
for r in conn.execute("SELECT * FROM daemon_audit_events ORDER BY id DESC LIMIT 20").fetchall():
    print(" ", r)

print("\n--- signals ---")
for r in conn.execute("SELECT * FROM signals ORDER BY id DESC LIMIT 20").fetchall():
    print(" ", r)

conn.close()
