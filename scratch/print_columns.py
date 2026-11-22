import sqlite3
import os

p = 'C:/Users/sebas/AppData/Local/BlackDaemonFx/trading_bot.sqlite3'
conn = sqlite3.connect(f"file:{p}?mode=ro", uri=True)
cur = conn.cursor()

print("Columns in signals:")
cur.execute("PRAGMA table_info(signals)")
print([c[1] for c in cur.fetchall()])

print("Columns in daemon_audit_events:")
cur.execute("PRAGMA table_info(daemon_audit_events)")
print([c[1] for c in cur.fetchall()])

print("Columns in trades:")
cur.execute("PRAGMA table_info(trades)")
print([c[1] for c in cur.fetchall()])

print("\n--- SAMPLE RECENT SIGNAL ---")
cur.execute("SELECT * FROM signals ORDER BY id DESC LIMIT 1")
cols = [d[0] for d in cur.description]
print(dict(zip(cols, cur.fetchone())))

print("\n--- SAMPLE RECENT AUDIT EVENT ---")
cur.execute("SELECT * FROM daemon_audit_events ORDER BY id DESC LIMIT 1")
cols = [d[0] for d in cur.description]
print(dict(zip(cols, cur.fetchone())))

print("\n--- SAMPLE RECENT TRADE ---")
cur.execute("SELECT * FROM trades ORDER BY id DESC LIMIT 1")
cols = [d[0] for d in cur.description]
print(dict(zip(cols, cur.fetchone())))

conn.close()
