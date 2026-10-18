import sqlite3
import json

conn = sqlite3.connect(r"file:C:\Users\sebas\AppData\Local\BlackDaemonFx\trading_bot.sqlite3?mode=ro", uri=True)
conn.row_factory = sqlite3.Row
cur = conn.cursor()

signals = cur.execute("SELECT * FROM signals ORDER BY id DESC LIMIT 5").fetchall()
for s in signals:
    print(f"\n--- Signal {s['id']}: {s['instrument']} {s['direction']} (TF: {s['timeframe']}) ---")
    print(f"Valid: {s['valid']} | Trend: {s['trend_ok']} | Liquidity: {s['liquidity_ok']} | OB: {s['order_block_ok']} | Retest: {s['retest_ok']}")
    if s['details_json']:
        try:
            d = json.loads(s['details_json'])
            print(f"Details: {json.dumps(d, indent=2)[:300]}...")
        except:
            print(f"Details (raw): {s['details_json'][:200]}")
