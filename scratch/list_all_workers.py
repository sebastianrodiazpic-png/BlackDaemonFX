import sqlite3

live_db = r"C:\Users\sebas\AppData\Local\BlackDaemonFx\trading_bot.sqlite3"
conn = sqlite3.connect(f"file:{live_db}?mode=ro", uri=True)
cur = conn.cursor()

cur.execute("SELECT id, source, bot_profile, daemon_magic, status, pid, current_symbol, last_action, last_event_time FROM worker_runtime_states")
rows = cur.fetchall()
print(f"Total workers: {len(rows)}")
for r in rows:
    print(r)

print("\n--- DETALLES DE TRADES RECIENTES DE ORB ---")
cur.execute("SELECT id, external_ticket, broker_position_ticket, instrument, direction, status, result, entry_time, exit_time, setup_reason, details_json FROM trades WHERE setup_reason LIKE '%ORB%' OR details_json LIKE '%ORB%' ORDER BY id DESC LIMIT 5")
for t in cur.fetchall():
    print(f"ID: {t[0]}, Ticket: {t[1]}/{t[2]}, Symbol: {t[3]}, Dir: {t[4]}, Status: {t[5]}, Res: {t[6]}")
    print(f"  Entry: {t[7]}, Exit: {t[8]}")
    print(f"  Setup: {t[9]}")
    # let's parse details_json
    import json
    try:
        dj = json.loads(t[10])
        # look for execution key, worker, magic, etc.
        print(f"  Magic: {dj.get('metadata', {}).get('mt5_magic') or dj.get('post_fill_risk', {}).get('magic')}")
        print(f"  Details keys: {list(dj.keys())}")
        if 'execution_key' in dj:
            print(f"  Execution key: {dj.get('execution_key')}")
        if 'market_snapshot' in dj.get('metadata', {}):
            print(f"  Snapshot: {dj.get('metadata', {}).get('market_snapshot')}")
        # print first 300 chars of details
        print(f"  Raw sample: {t[10][:300]}")
    except Exception as e:
        print(f"  JSON parse error: {e}")

conn.close()
