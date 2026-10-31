import sqlite3
import os
import json

paths = [
    'storage/trading_bot.db',
    'database/trading_bot.sqlite3',
    os.path.expandvars(r'%LOCALAPPDATA%\BlackDaemonFx\trading_bot.sqlite3')
]

for p in paths:
    if os.path.exists(p) and os.path.getsize(p) > 0:
        print(f"=== DB: {p} ({os.path.getsize(p)} bytes) ===")
        try:
            conn = sqlite3.connect(f"file:{os.path.abspath(p)}?mode=ro", uri=True)
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [r[0] for r in cursor.fetchall()]
            for t in tables:
                cursor.execute(f"SELECT COUNT(*) FROM {t}")
                cnt = cursor.fetchone()[0]
                print(f"  - {t}: {cnt} rows")
            conn.close()
        except Exception as e:
            print(f"  Error reading: {e}")
    else:
        print(f"=== DB: {p} (NOT FOUND or 0 bytes) ===")
