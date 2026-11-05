import sqlite3
from collections import Counter
import json

db_path = r"C:\Users\sebas\AppData\Local\BlackDaemonFx\trading_bot.sqlite3"
con = sqlite3.connect(db_path)
cur = con.cursor()

print("=== FREQUENCY OF REASONS ACROSS PROFILES (LAST 10000 AUDIT EVENTS) ===")
cur.execute("""
    SELECT source, event_type, instrument, reason, action 
    FROM daemon_audit_events 
    ORDER BY id DESC 
    LIMIT 10000
""")
rows = cur.fetchall()

reasons_by_profile = {}
for r in rows:
    # try parsing payload for bot_profile
    profile = r[0]
    reason = r[3]
    action = r[4]
    ev_type = r[1]
    if reason:
        reasons_by_profile.setdefault(ev_type, Counter())[reason] += 1

print("\n--- TOP REASONS BY EVENT TYPE ---")
for ev, counts in reasons_by_profile.items():
    if sum(counts.values()) > 20:
        print(f"\n[Event: {ev}] Total: {sum(counts.values())}")
        for r, c in counts.most_common(5):
            print(f"  ({c}x) {r}")

print("\n=== RECENT WAITING/REJECTED ACTIONS FROM WORKER RUNTIME STATES ===")
cur.execute("SELECT bot_profile, last_action, last_reason, symbols_total, symbols_processed FROM worker_runtime_states")
for w in cur.fetchall():
    print(f"Worker {w[0]}: Action={w[1]} | Reason={w[2]} | Scanned={w[4]}/{w[3]}")
