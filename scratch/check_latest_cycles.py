import sqlite3, json

conn = sqlite3.connect(r'C:\Users\sebas\AppData\Local\BlackDaemonFx\trading_bot.sqlite3')

print("Latest DAEMON_CYCLE_START events:")
rows = conn.execute("SELECT id, event_type, action, payload_json, created_at FROM daemon_audit_events WHERE event_type='DAEMON_CYCLE_START' ORDER BY id DESC LIMIT 15").fetchall()
for r in rows:
    p = json.loads(r[3])
    if p.get("configured_symbols_count") in (60, 25, 23, 21):
        print(f"Cycle id={r[0]}, created_at={r[4]}, symbols_count={p.get('symbols_count')}, configured={p.get('configured_symbols_count')}, selected={p.get('selected_symbols_count')}")

print("\nLatest MALAYSIAN_SNR trades:")
trades = conn.execute("SELECT id, instrument, bot_profile, status, entry_price, sl_price, tp1_price, opened_at FROM trades WHERE bot_profile='MALAYSIAN_SNR' ORDER BY id DESC LIMIT 5").fetchall()
for t in trades:
    print(t)
