import sqlite3
import json
from pathlib import Path

db_path = Path.home() / 'AppData/Local/BlackDaemonFx/trading_bot.sqlite3'
conn = sqlite3.connect(f'file:{db_path}?mode=ro', uri=True)
conn.row_factory = sqlite3.Row
cur = conn.cursor()

# Query our signals of interest
query = """
SELECT id, instrument, timeframe, signal_time, created_at, details_json
FROM signals
WHERE id IN (21235, 21236, 21240, 21241, 21242, 21243, 21244, 21248, 21250, 21268, 21272, 21279, 21286, 21290)
ORDER BY id ASC
"""
cur.execute(query)
rows = cur.fetchall()

print("=" * 100)
print("TIMING FORENSICS IN signals TABLE (trading_bot.sqlite3)")
print("=" * 100)

for r in rows:
    dt = {}
    if r['details_json']:
        try:
            dt = json.loads(r['details_json'])
        except Exception:
            pass
            
    print(f"\nSignal ID: {r['id']} | {r['instrument']} | TF: {r['timeframe']}")
    print(f"  signal_time: {r['signal_time']}")
    print(f"  created_at : {r['created_at']}")
    
    # Inspect any timing fields in details_json
    timing_keys = [k for k in dt.keys() if 'time' in k.lower() or 'at' in k.lower() or 'date' in k.lower()]
    print(f"  timing fields in details_json:")
    for k in timing_keys:
        print(f"    - {k}: {dt[k]}")
        
    # Check if there is entry_learning_snapshot or meta_label
    meta = dt.get('meta_label') or {}
    learning = dt.get('entry_learning_snapshot') or {}
    if meta:
        print(f"    - meta_label.evaluated_at: {meta.get('evaluated_at')}")
    if learning:
        print(f"    - learning.captured_at: {learning.get('captured_at')}")
        timing_sub = learning.get('timing') or {}
        for tk, tv in timing_sub.items():
            print(f"    - learning.timing.{tk}: {tv}")

conn.close()
