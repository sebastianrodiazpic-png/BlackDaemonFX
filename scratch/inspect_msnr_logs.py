import sqlite3

conn = sqlite3.connect("data/trading_bot.db")
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

for tbl in ["worker_runtime_states", "daemon_audit_events", "signals"]:
    cursor.execute(f"PRAGMA table_info({tbl})")
    cols = [r["name"] for r in cursor.fetchall()]
    print(f"Columnas en {tbl}:", cols)

print("\n=== WORKER RUNTIME STATES (TODOS LOS REGISTROS) ===")
cursor.execute("SELECT * FROM worker_runtime_states")
for r in cursor.fetchall():
    d = dict(r)
    print(f"Profile: {d.get('bot_profile')} | PID: {d.get('pid')} | Magic: {d.get('daemon_magic')} | Sym: {d.get('current_symbol')} | Cycle: {d.get('cycle_number')} | Act: {d.get('last_action')} | Reason: {d.get('last_reason')}")

conn.close()
