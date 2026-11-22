import sqlite3
import json

p = 'C:/Users/sebas/AppData/Local/BlackDaemonFx/trading_bot.sqlite3'
conn = sqlite3.connect(f"file:{p}?mode=ro", uri=True)
cur = conn.cursor()

print("=== DETALLES DE TRADES #1813 Y #1814 ===")
cur.execute("SELECT id, external_ticket, broker_position_ticket, instrument, direction, status, entry_price, stop_loss, take_profit, volume, setup_reason, details_json, created_at FROM trades WHERE id IN (1813, 1814)")
cols = [d[0] for d in cur.description]
for r in cur.fetchall():
    row = dict(zip(cols, r))
    details = {}
    if row.get('details_json'):
        try:
            details = json.loads(row['details_json'])
        except Exception:
            pass
    print(f"\nTrade #{row['id']} | {row['instrument']} {row['direction']} | Volume: {row['volume']}")
    print(f"  Entry: {row['entry_price']} | SL: {row['stop_loss']} | TP: {row['take_profit']}")
    print(f"  Setup Reason: {row['setup_reason']}")
    print(f"  Status: {row['status']} | Created: {row['created_at']}")
    tc = details.get('tripartite_confluence')
    if tc:
        print(f"  Tripartite Confluence: allowed={tc.get('allowed')} | action={tc.get('action')} | score={tc.get('human_criteria_score')} | reason={tc.get('reason')}")
    hc = details.get('human_criteria')
    if hc:
        print(f"  Human Criteria: score={hc.get('score')} | grade={hc.get('grade')}")

conn.close()
