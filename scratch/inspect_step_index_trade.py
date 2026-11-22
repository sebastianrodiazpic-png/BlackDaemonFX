import sqlite3
import json

db_path = "storage/trading_bot.sqlite3"
conn = sqlite3.connect(db_path)
conn.row_factory = sqlite3.Row
cur = conn.cursor()

print("--- BUSCANDO TRADES DE STEP INDEX ---")
cur.execute("PRAGMA table_info(trades)")
cols = [c[1] for c in cur.fetchall()]
print("Columnas de trades:", cols)

sym_col = "instrument" if "instrument" in cols else "symbol"
cur.execute(f"SELECT * FROM trades WHERE {sym_col} LIKE '%Step%' ORDER BY id DESC LIMIT 10")
rows = cur.fetchall()
print(f"Total encontrados: {len(rows)}")

for r in rows:
    d = dict(r)
    print("\n-------------------------------------------")
    print(f"ID: {d.get('id')} | Ticket: {d.get('ticket')} | Magic: {d.get('magic')} | Symbol: {d.get('symbol')} | Status: {d.get('status')}")
    print(f"Type: {d.get('trade_type') or d.get('order_type')} | Leg: {d.get('trade_leg') or d.get('leg')}")
    print(f"Open Price: {d.get('open_price')} | Open Time: {d.get('open_time')}")
    print(f"SL: {d.get('stop_loss')} | TP: {d.get('take_profit')}")
    print(f"RR: {d.get('target_rr')} | Risk Amount: {d.get('risk_amount')} | Volume: {d.get('volume')}")
    print(f"Comment: {d.get('comment')}")
    
    # Metadata
    meta = d.get('metadata')
    if meta:
        try:
            m = json.loads(meta)
            print("Metadata:", json.dumps({k: v for k, v in m.items() if k in ('strategy_name', 'trade_leg', 'first_target_rr', 'second_target_rr', 'entry_price', 'stop_loss', 'tp1_price', 'tp2_price', 'broker_tp', 'risk_distance', 'target_distance', 'planned_rr', 'actual_rr', 'runner_target_rr', 'risk_metrics')}, indent=2))
        except:
            print("Raw meta:", meta[:200])

conn.close()
