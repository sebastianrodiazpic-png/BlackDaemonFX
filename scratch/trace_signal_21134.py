import sqlite3, json

conn = sqlite3.connect(r'C:\Users\sebas\AppData\Local\BlackDaemonFx\trading_bot.sqlite3')
sig = conn.execute('SELECT id, instrument, direction, details_json FROM signals WHERE id=21134').fetchone()
print(f"Signal ID: {sig[0]}, Instrument: {sig[1]}, Dir: {sig[2]}")
if sig[3]:
    p = json.loads(sig[3])
    print("Strategy:", p.get("strategy_name"))
    print("Scenario:", p.get("scenario"))
    print("Score:", p.get("trade_score"))
    print("Confirmations:", p.get("confirmations"))

max_id = conn.execute('SELECT max(id) FROM daemon_audit_events').fetchone()[0]
events = conn.execute(f"""
    SELECT id, event_type, action, created_at, payload_json 
    FROM daemon_audit_events 
    WHERE id >= {max_id - 25000}
      AND payload_json LIKE '%Jump 25 Index%'
    ORDER BY id DESC LIMIT 10
""").fetchall()

print(f"\nAudit events for Jump 25 Index ({len(events)}):")
for e in events:
    print(f"[{e[3]}] ID={e[0]} | Type={e[1]} | Action={e[2]}")
    try:
        p = json.loads(e[4])
        print(" ", p)
    except Exception:
        print(" ", str(e[4])[:120])
