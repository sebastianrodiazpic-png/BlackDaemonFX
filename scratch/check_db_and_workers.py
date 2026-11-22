import sqlite3
import glob
from datetime import datetime

for db in glob.glob("storage/*.sqlite3") + glob.glob("storage/*.db"):
    print(f"\n==========================================")
    print(f"DATABASE: {db}")
    print(f"==========================================")
    try:
        con = sqlite3.connect(db)
        cur = con.cursor()
        cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [r[0] for r in cur.fetchall()]
        print("Tables:", tables)

        if "worker_runtime_states" in tables:
            print("\n--- worker_runtime_states ---")
            cur.execute("SELECT bot_profile, daemon_magic, status, last_action, last_reason, updated_at FROM worker_runtime_states ORDER BY updated_at DESC LIMIT 15")
            for r in cur.fetchall():
                print(r)

        if "audit_log" in tables:
            print("\n--- audit_log (últimos 5) ---")
            cur.execute("SELECT event_type, instrument, action, reason, timestamp FROM audit_log ORDER BY id DESC LIMIT 5")
            for r in cur.fetchall():
                print(r)

        if "trades" in tables:
            cur.execute("SELECT COUNT(*) FROM trades")
            print("\nTotal trades:", cur.fetchone()[0])
            cur.execute("SELECT status, COUNT(*) FROM trades GROUP BY status")
            print("Trades by status:", cur.fetchall())

    except Exception as e:
        print("Error reading db:", e)
