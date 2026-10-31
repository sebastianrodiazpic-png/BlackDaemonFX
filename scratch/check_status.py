import sqlite3
import os
import glob
from datetime import datetime

dbs = [
    'storage/trading_bot.db',
    'database/trading_bot.sqlite3',
    'trading_bot.db',
    'trading_bot.sqlite3',
    os.path.expandvars(r'%LOCALAPPDATA%\BlackDaemonFx\trading_bot.sqlite3')
]

print("=== INSPECTING DATABASES ===")
for db_path in dbs:
    if not os.path.exists(db_path):
        print(f"[-] Not found: {db_path}")
        continue
    size = os.path.getsize(db_path)
    mtime = datetime.fromtimestamp(os.path.getmtime(db_path)).isoformat()
    print(f"\n[+] DB: {db_path} (Size: {size} bytes, Mtime: {mtime})")
    try:
        conn = sqlite3.connect(db_path)
        cur = conn.cursor()
        cur.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = [r[0] for r in cur.fetchall()]
        print(f"    Tables: {tables}")
        for t in tables:
            try:
                cur.execute(f'SELECT count(*) FROM "{t}"')
                cnt = cur.fetchone()[0]
                print(f"      - {t}: {cnt} rows")
            except Exception as e:
                print(f"      - {t}: error ({e})")
        
        # Check trades/positions/executions
        for t in ['trades', 'positions', 'orders', 'trade_executions', 'signals']:
            if t in tables:
                cur.execute(f'SELECT * FROM "{t}" ORDER BY rowid DESC LIMIT 5')
                rows = cur.fetchall()
                col_names = [d[0] for d in cur.description]
                print(f"    Sample last 5 rows of {t} ({col_names}):")
                for r in rows:
                    print("       ", r)
        conn.close()
    except Exception as e:
        print(f"    Error reading: {e}")
