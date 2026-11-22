import sqlite3

conn = sqlite3.connect("storage/trading_bot.sqlite3")
cur = conn.cursor()

print("--- strategy_runtime_preferences ---")
try:
    for r in cur.execute("SELECT * FROM strategy_runtime_preferences").fetchall():
        print(r)
except Exception as e:
    print(e)

print("--- worker_runtime_states ---")
try:
    for r in cur.execute("SELECT bot_profile, status, last_action, last_reason, updated_at FROM worker_runtime_states").fetchall():
        print(r)
except Exception as e:
    print(e)

print("--- instrument_selection_profile_preferences ---")
try:
    for r in cur.execute("SELECT selection_profile, selected_symbols, updated_at FROM instrument_selection_profile_preferences").fetchall():
        print(r[0], len(r[1]), r[2])
except Exception as e:
    print(e)

conn.close()
