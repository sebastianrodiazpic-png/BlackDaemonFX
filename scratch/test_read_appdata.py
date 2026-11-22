import os
import sqlite3
import pandas as pd

appdata_db = os.path.expandvars(r"%LOCALAPPDATA%\BlackDaemonFx\trading_bot.sqlite3")
print("AppData DB exists:", os.path.exists(appdata_db))
if os.path.exists(appdata_db):
    try:
        conn = sqlite3.connect(f"file:{appdata_db}?mode=ro", uri=True)
        cur = conn.cursor()
        print("Trades count:", cur.execute("SELECT COUNT(1) FROM trades").fetchone()[0])
        print("Audit events count:", cur.execute("SELECT COUNT(1) FROM daemon_audit_events").fetchone()[0])
        
        q_types = cur.execute("SELECT event_type, COUNT(1) FROM daemon_audit_events GROUP BY event_type").fetchall()
        print("\nAudit event types:")
        for t, c in q_types:
            print(f"  {t}: {c}")
    except Exception as e:
        print("Error reading AppData DB:", e)
