import sqlite3, os
from pathlib import Path

db_path = Path(os.environ.get('LOCALAPPDATA', '')) / 'BlackDaemonFx' / 'trading_bot.sqlite3'
conn = sqlite3.connect(f"file:{db_path.as_posix()}?mode=ro", uri=True)
conn.row_factory = sqlite3.Row
cur = conn.cursor()

print("================ INSPECT 'OTHER/MANUAL' TRADES ================")
cur.execute("""
    SELECT id, execution_key, instrument, direction, source, setup_reason, details_json, realized_rr, net_pnl, created_at
    FROM trades
    WHERE (execution_key NOT LIKE '%MSNR%' AND setup_reason NOT LIKE '%MSNR%')
      AND (execution_key NOT LIKE '%ICT%' AND setup_reason NOT LIKE '%ICT%')
      AND (execution_key NOT LIKE '%ORB%' AND setup_reason NOT LIKE '%ORB%')
      AND (execution_key NOT LIKE '%CARRY%')
      AND (execution_key NOT LIKE '%RSI2%')
      AND (execution_key NOT LIKE '%TREND%')
    ORDER BY id DESC
    LIMIT 10
""")
for r in cur.fetchall():
    print(f"ID #{r['id']} | key={r['execution_key']} | {r['instrument']} {r['direction']} | src={r['source']} | R={r['realized_rr']} | pnl={r['net_pnl']}")
    print(f"   setup_reason: {r['setup_reason']}")
    print(f"   details_sample: {str(r['details_json'])[:120]}")

conn.close()
