import sqlite3
import json
from pathlib import Path

db_path = Path.home() / 'AppData/Local/BlackDaemonFx/trading_bot.sqlite3'
conn = sqlite3.connect(f'file:{db_path}?mode=ro', uri=True)
conn.row_factory = sqlite3.Row
cur = conn.cursor()

# Query ICT signals
query = """
SELECT id, instrument, timeframe, signal_time, created_at, details_json
FROM signals
WHERE id IN (21235, 21236, 21240, 21241, 21242, 21243, 21244, 21248, 21250)
ORDER BY id ASC
"""
cur.execute(query)
rows = cur.fetchall()

print("=" * 100)
print("TIMING FORENSICS FOR ICT SIGNALS IN signals TABLE (trading_bot.sqlite3)")
print("=" * 100)

for r in rows:
    dt = {}
    if r['details_json']:
        try:
            dt = json.loads(r['details_json'])
        except Exception:
            pass
            
    print(f"\nSignal ID: {r['id']} | {r['instrument']} | TF: {r['timeframe']}")
    print(f"  signal_time : {r['signal_time']}")
    print(f"  created_at  : {r['created_at']}")
    print(f"  evaluated_at: {dt.get('evaluated_at')}")
    print(f"  detected_at : {dt.get('detected_at')}")
    print(f"  entry_time  : {dt.get('entry_time')}")
    strategy = dt.get('strategy_name') or dt.get('strategy')
    print(f"  strategy    : {strategy}")

conn.close()
