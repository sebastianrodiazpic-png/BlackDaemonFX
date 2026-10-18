import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import sqlite3
import pandas as pd
from database.database import resolve_db_path

db_path = resolve_db_path()
print(f"Target DB Path: {db_path}")

conn = sqlite3.connect(f"file:{db_path.as_posix()}?mode=ro", uri=True)
cursor = conn.cursor()

tables = [r[0] for r in cursor.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()]
print(f"Found {len(tables)} tables: {tables}")

# Check trades by strategy
print("\n--- Trades count by strategy ---")
try:
    df_trades = pd.read_sql_query("SELECT strategy, count(*) as count FROM trades GROUP BY strategy", conn)
    print(df_trades)
except Exception as e:
    print(f"Error querying trades: {e}")

# Check trade journal by strategy
print("\n--- Trade journal count by strategy ---")
try:
    df_journal = pd.read_sql_query("SELECT strategy, count(*) as count FROM trade_journal GROUP BY strategy", conn)
    print(df_journal)
except Exception as e:
    print(f"Error querying trade_journal: {e}")

# Check any msnr occurrences in trades
print("\n--- Any msnr in trades ---")
try:
    df_msnr = pd.read_sql_query("SELECT * FROM trades WHERE lower(strategy) LIKE '%snr%' OR lower(strategy) LIKE '%msnr%'", conn)
    print(f"MSNR trades count: {len(df_msnr)}")
    if len(df_msnr) > 0:
        print(df_msnr.head())
except Exception as e:
    print(e)

# Check strategy configurations / settings table
for t in tables:
    if any(k in t.lower() for k in ['setting', 'config', 'runtime', 'strategy', 'preference', 'model', 'ai', 'audit', 'signal']):
        count = cursor.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
        print(f"Table {t}: {count} rows")

conn.close()
