import sqlite3
import glob
from pathlib import Path

for db in glob.glob("storage/*.sqlite3") + glob.glob("storage/*.db"):
    print("=" * 60)
    print("DB:", db)
    try:
        conn = sqlite3.connect(db)
        cur = conn.cursor()
        tables = [r[0] for r in cur.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()]
        print("Tables:", tables)
        if "worker_states" in tables:
            print("--- worker_states ---")
            for r in cur.execute("SELECT bot_profile, status, last_action, last_reason, updated_at FROM worker_states ORDER BY updated_at DESC").fetchall()[:25]:
                print(r)
        if "signals" in tables:
            print("--- recent signals ---")
            for r in cur.execute("SELECT symbol, strategy, direction, status, created_at, rejection_reason FROM signals ORDER BY created_at DESC LIMIT 20").fetchall():
                print(r)
        if "trades" in tables:
            print("--- recent trades ---")
            for r in cur.execute("SELECT symbol, strategy_name, direction, status, open_time, pnl, comment FROM trades ORDER BY open_time DESC LIMIT 20").fetchall():
                print(r)
        conn.close()
    except Exception as e:
        print("Error:", e)
