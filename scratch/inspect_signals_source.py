import sqlite3
import json
from pathlib import Path
import pandas as pd

live_db = Path.home() / "AppData/Local/BlackDaemonFx/trading_bot.sqlite3"
conn = sqlite3.connect(f"file:{live_db.resolve()}?mode=ro", uri=True)
cur = conn.cursor()

ids = [21234, 21237, 21252, 21255, 21257, 21260, 21268, 21272, 21279, 21286, 21290, 21299, 21302]
cur.execute(f"""
    SELECT id, instrument, timeframe, signal_time, direction, valid, created_at, details_json
    FROM signals
    WHERE id IN ({','.join(map(str, ids))})
    ORDER BY id ASC
""")

rows = cur.fetchall()
print(f"Total matching signals: {len(rows)}")
for r in rows:
    det = json.loads(r[7]) if r[7] else {}
    strategy = "MSNR" if "setup_type" in det or "msnr" in str(det).lower() else "ICT"
    print(f"ID: {r[0]:<5} | Strat: {strategy:<4} | Inst: {r[1]:<15} | TF: {r[2]:<3} | SigTime: {r[3]} | CreatedAt: {r[6]} | Dir: {r[4]} | Valid: {r[5]} | Entry: {det.get('entry_price')} | SL: {det.get('stop_loss')} | TP1: {det.get('take_profit_1')} | TP2: {det.get('take_profit_2')}")
conn.close()
