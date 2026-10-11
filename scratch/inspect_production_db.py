import sys
sys.path.insert(0, ".")

from database.database import database_diagnostics, resolve_db_path
from database.repository import TradingRepository
import sqlite3
import json

diag = database_diagnostics()
print("=== DATABASE DIAGNOSTICS ===")
for k, v in diag.items():
    print(f"  {k}: {v}")

real_path = resolve_db_path()
print("\nREAL DB PATH:", real_path)

conn = sqlite3.connect(str(real_path))
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
tables = [row["name"] for row in cursor.fetchall()]
print("Tablas en DB Real:", tables)

if "worker_runtime_states" in tables:
    print("\n=== WORKER RUNTIME STATES (DB REAL) ===")
    cursor.execute("SELECT * FROM worker_runtime_states")
    workers = cursor.fetchall()
    print(f"Total workers: {len(workers)}")
    for w in workers:
        d = dict(w)
        print(f"[{d.get('bot_profile')}] PID: {d.get('pid')} | Magic: {d.get('daemon_magic')} | Sym: {d.get('current_symbol')} | Ciclo: {d.get('cycle_number')} | Acc: {d.get('last_action')} | Reason: {d.get('last_reason')} | Update: {d.get('updated_at')}")

if "daemon_audit_events" in tables:
    print("\n=== DAEMON AUDIT EVENTS RECIENTES ===")
    cursor.execute("SELECT * FROM daemon_audit_events ORDER BY id DESC LIMIT 20")
    for r in cursor.fetchall():
        d = dict(r)
        print(f"[{d.get('created_at')}] Event: {d.get('event_type')} | Daemon: {d.get('source')} | Sym: {d.get('instrument')} | Act: {d.get('action')} | Reason: {d.get('reason')}")

conn.close()
