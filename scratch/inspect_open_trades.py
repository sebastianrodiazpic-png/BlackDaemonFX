import sqlite3
import os
import json
from pathlib import Path

p = Path(os.environ['LOCALAPPDATA']) / 'BlackDaemonFx' / 'trading_bot.sqlite3'
conn = sqlite3.connect(p)
cur = conn.cursor()

cur.execute("SELECT id, instrument, direction, entry_price, stop_loss, take_profit, planned_rr, entry_time, setup_reason, details_json FROM trades WHERE status = 'OPEN'")
rows = cur.fetchall()
print(f"Total open trades: {len(rows)}")
for r in rows:
    print(f"=== OPEN Trade #{r[0]} | {r[1]} {r[2]} | Entry: {r[7]} ===")
    print(f"Entry: {r[3]} | SL: {r[4]} | TP: {r[5]} | Planned RR: {r[6]}")
    if r[9]:
        try:
            details = json.loads(r[9])
            meta = details.get('metadata', {})
            print("  mae_price:", meta.get('mae_price'), "mfe_price:", meta.get('mfe_price'))
            print("  last_sample_rr:", meta.get('excursion_last_sample_rr'))
        except Exception as e:
            print("  err:", e)
conn.close()
