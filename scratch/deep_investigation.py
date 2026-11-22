import sqlite3
import os
import glob
from datetime import datetime

db_path = "storage/trading_bot.sqlite3"
print(f"=== DB INSPECTION: {db_path} ===")
conn = sqlite3.connect(db_path)
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = [row["name"] for row in cursor.fetchall()]
print("Tables found:", tables)

for t in tables:
    try:
        cursor.execute(f'SELECT COUNT(*) as c FROM "{t}"')
        cnt = cursor.fetchone()["c"]
        print(f"Table {t}: {cnt} rows")
    except Exception as e:
        print(f"Table {t} error: {e}")

# Check columns and sample data of trades, signals, position_visual_audits, trade_journal, etc.
for target in ["trades", "signals", "position_visual_audits", "trade_journal", "account_metrics"]:
    if target in tables:
        cursor.execute(f"PRAGMA table_info('{target}')")
        cols = [col["name"] for col in cursor.fetchall()]
        print(f"\n--- Schema {target} ---")
        print(", ".join(cols))
        
        cursor.execute(f"SELECT * FROM '{target}' ORDER BY rowid DESC LIMIT 5")
        rows = cursor.fetchall()
        print(f"Recent {len(rows)} entries in {target}:")
        for r in rows:
            d = dict(r)
            # print compact representation
            summary = {k: v for k, v in d.items() if v is not None and k in ['id', 'ticket', 'symbol', 'strategy', 'direction', 'profit', 'r_multiple', 'pnl', 'status', 'created_at', 'opened_at', 'closed_at', 'rejection_reason', 'score', 'verdict', 'reason']}
            print("  ", summary if summary else list(d.items())[:6])

conn.close()
