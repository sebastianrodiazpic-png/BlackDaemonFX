import sqlite3
import datetime
import json

now = datetime.datetime.now()
target = now.replace(hour=12, minute=0, second=0, microsecond=0)
diff_sec = (target - now).total_seconds()
print(f"Current local time: {now}")
print(f"Target 12:00: {target}")
print(f"Seconds to 12:00: {diff_sec:.1f}")

db_path = r"C:\Users\sebas\AppData\Local\BlackDaemonFx\trading_bot.sqlite3"
conn = sqlite3.connect(db_path)
conn.row_factory = sqlite3.Row
cur = conn.cursor()

print(f"\n--- Checking Open Ticket 4757414460 ---")
row = cur.execute("SELECT * FROM trades WHERE broker_position_ticket = 4757414460").fetchone()
if row:
    for k in row.keys():
        print(f"  {k}: {row[k]}")
else:
    print("  Ticket not yet recorded in trades table. Checking audit events...")
    evs = cur.execute("SELECT * FROM daemon_audit_events WHERE payload_json LIKE '%4757414460%' ORDER BY id DESC LIMIT 5").fetchall()
    for e in evs:
        print(f"  Event: {e['event_type']} | {e['payload_json']}")

print(f"\n--- Detailed Breakdown of Today's Trades (2026-10-15) ---")
today_trades = cur.execute("SELECT * FROM trades WHERE entry_time >= '2026-10-15 00:00:00' ORDER BY id ASC").fetchall()
for t in today_trades:
    print(f"\n>>> Trade ID {t['id']} | Ticket {t['broker_position_ticket']} | {t['instrument']} | {t['direction']}")
    print(f"    Strategy: {t['strategy_version']} | Exit Reason: {t['exit_reason']}")
    print(f"    Volume: {t['volume']} | PnL: ${t['net_pnl']} | Planned RR: {t['planned_rr']} | Realized RR: {t['realized_rr']}")
    print(f"    Entry Price: {t['entry_price']} | Exit Price: {t['exit_price']} | SL: {t['stop_loss']} | TP: {t['take_profit']}")
    print(f"    Entry Time: {t['entry_time']} | Exit Time: {t['exit_time']}")
    print(f"    Setup Reason: {t['setup_reason']}")
    if t['details_json']:
        try:
            det = json.loads(t['details_json'])
            print(f"    Details: {json.dumps(det, indent=6)}")
        except Exception as ex:
            print(f"    Details (raw): {t['details_json']}")

