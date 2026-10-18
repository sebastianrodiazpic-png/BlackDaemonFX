import sqlite3
import json

conn = sqlite3.connect(r'C:\Users\sebas\AppData\Local\BlackDaemonFx\trading_bot.sqlite3')
rows = conn.execute('''
    SELECT id, broker_position_ticket, broker_order_ticket, instrument, direction, volume, 
           entry_price, stop_loss, take_profit, planned_rr, risk_percent, risk_amount, details_json
    FROM trades WHERE status = 'OPEN'
''').fetchall()

for r in rows:
    print(f"ID: {r[0]} | PosTicket: {r[1]} | OrdTicket: {r[2]} | Sym: {r[3]} | Dir: {r[4]} | Vol: {r[5]}")
    print(f"  Entry: {r[6]} | SL: {r[7]} | TP: {r[8]} | RR: {r[9]} | RiskPct: {r[10]} | RiskAmt: {r[11]}")
    details = json.loads(r[12]) if r[12] else {}
    print(f"  metadata: {details.get('metadata')}")
    print(f"  split_context: {details.get('split_context')}")
