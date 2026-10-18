import sqlite3
from pathlib import Path

db_path = Path.home() / 'AppData/Local/BlackDaemonFx/trading_bot.sqlite3'
conn = sqlite3.connect(f'file:{db_path}?mode=ro', uri=True)
cur = conn.cursor()
cur.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='signals'")
row = cur.fetchone()
print(row[0] if row else 'Table signals not found')
conn.close()
