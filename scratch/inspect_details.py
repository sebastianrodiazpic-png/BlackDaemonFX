import sqlite3
import json

conn = sqlite3.connect(r'C:\Users\sebas\AppData\Local\BlackDaemonFx\trading_bot.sqlite3')
cur = conn.cursor()
rows = cur.execute("SELECT id, broker_position_ticket, instrument, risk_percent, risk_amount, planned_rr, details_json FROM trades WHERE status='OPEN'").fetchall()
for r in rows:
    details = json.loads(r[6]) if r[6] else {}
    meta = details.get('metadata', {})
    print(f"ID={r[0]} Ticket={r[1]} Symbol={r[2]} Risk%={r[3]} Risk$={r[4]} PlannedRR={r[5]}")
    print(f"  Leg={meta.get('trade_leg')} Strategy={meta.get('strategy_name')} BE_trigger_rr={meta.get('break_even_trigger_rr')} target_rr={meta.get('target_rr')} logical_target_rr={meta.get('logical_target_rr')}")
