import sqlite3
from pathlib import Path

db_path = Path("storage/trading_bot.sqlite3")
conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
cur = conn.cursor()

synth_filter = "(instrument LIKE '%Index%' OR instrument LIKE '%Volatility%' OR instrument LIKE '%Step%' OR instrument LIKE '%Boom%' OR instrument LIKE '%Crash%' OR instrument LIKE '%Jump%')"

print("=== WORKER RUNTIME STATES ===")
cur.execute("SELECT bot_profile, status, last_action, last_reason, updated_at FROM worker_runtime_states ORDER BY updated_at DESC;")
for r in cur.fetchall():
    print(r)

print("\n=== DAEMON AUDIT EVENTS (SYNTHETICS) ===")
cur.execute(f"SELECT created_at, instrument, action, reason FROM daemon_audit_events WHERE {synth_filter} ORDER BY id DESC LIMIT 40;")
for r in cur.fetchall():
    print(f"[{r[0]}] {r[1]} -> Acción: {r[2]} | Motivo: {r[3]}")

print("\n=== REAZONES CON KILLZONE / ASIA / STANDBY / SESSION EN DAEMON AUDIT EVENTS ===")
cur.execute("SELECT DISTINCT instrument, action, reason FROM daemon_audit_events WHERE (reason LIKE '%KILLZONE%' OR reason LIKE '%ASIA%' OR reason LIKE '%STANDBY%' OR reason LIKE '%CLOSED%' OR reason LIKE '%SESSION%' OR action LIKE '%KILLZONE%' OR action LIKE '%STANDBY%');")
for r in cur.fetchall():
    print(r)

print("\n=== SIGNALS RECIENTES ===")
cur.execute("SELECT created_at, instrument, direction, valid FROM signals ORDER BY id DESC LIMIT 20;")
for r in cur.fetchall():
    print(f"[{r[0]}] {r[1]} {r[2]} | Valid: {r[3]}")

print("\n=== TRADES RECIENTES ===")
cur.execute("SELECT entry_time, instrument, direction, entry_price, status, setup_reason FROM trades ORDER BY id DESC LIMIT 20;")
for r in cur.fetchall():
    print(f"[{r[0]}] {r[1]} {r[2]} at {r[3]} | Status: {r[4]} | Reason: {r[5]}")

conn.close()
