import sqlite3
import json

live_db = r"C:\Users\sebas\AppData\Local\BlackDaemonFx\trading_bot.sqlite3"
conn = sqlite3.connect(f"file:{live_db}?mode=ro", uri=True)
cur = conn.cursor()

print("=== ACCOUNT SNAPSHOTS (ultimos 3) ===")
cur.execute("SELECT * FROM account_snapshots ORDER BY id DESC LIMIT 3")
cols = [c[0] for c in cur.description]
for r in cur.fetchall():
    d = dict(zip(cols, r))
    print(d)

print("\n=== TRADES RECIENTES: broker y cuenta ===")
cur.execute("SELECT id, source, broker, instrument, direction, status, entry_time, exit_time, net_pnl, setup_reason, details_json FROM trades ORDER BY id DESC LIMIT 5")
cols = [c[0] for c in cur.description]
for r in cur.fetchall():
    d = dict(zip(cols, r))
    dj = {}
    try:
        dj = json.loads(d['details_json'])
    except Exception:
        pass
    meta = dj.get('metadata', {})
    print(f"ID {d['id']}: {d['instrument']} {d['direction']} | Broker: {d['broker']} | Source: {d['source']} | Setup: {d['setup_reason']}")
    print(f"  Magic: {meta.get('mt5_magic')} | Comment: {meta.get('mt5_comment')} | Execution Mode: {meta.get('execution_mode')}")

conn.close()
