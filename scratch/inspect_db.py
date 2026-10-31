import sys
sys.path.insert(0, ".")
from database.database import resolve_db_path
import sqlite3

db_path = resolve_db_path()
print(f"=== DB PATH: {db_path} ===")

con = sqlite3.connect(db_path)
cur = con.cursor()
tables = [row[0] for row in cur.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()]
print("Tables:", tables)

for t in tables:
    count = cur.execute(f"SELECT count(*) FROM {t}").fetchone()[0]
    print(f"  {t}: {count} rows")

print("\n--- ULTIMOS TRADES ---")
cols = [c[1] for c in cur.execute("PRAGMA table_info(trades)").fetchall()]
trades = cur.execute("SELECT * FROM trades ORDER BY id DESC LIMIT 15").fetchall()
for t in trades:
    d = dict(zip(cols, t))
    print(" ", {k: d[k] for k in ["id", "symbol", "direction", "entry_price", "status", "created_at", "closed_at", "profit_usd", "net_r"] if k in d})

print("\n--- INSTRUMENT SELECTION PROFILES ---")
profiles = cur.execute("SELECT profile_name, active_instruments, updated_at FROM instrument_selection_profile_preferences").fetchall()
for p in profiles:
    print(f"Profile: {p[0]} (len={len(p[1]) if p[1] else 0}) -> {p[1][:120]}... updated: {p[2]}")

print("\n--- DAEMON AUDIT EVENTS (ultimos 10) ---")
events = cur.execute("SELECT id, worker, event_type, details, created_at FROM daemon_audit_events ORDER BY id DESC LIMIT 10").fetchall()
for e in events:
    print(f"  [{e[4]}] {e[1]} - {e[2]}: {str(e[3])[:100]}")
