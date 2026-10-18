import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import sqlite3
import pandas as pd
from database.database import resolve_db_path

db_path = resolve_db_path()
conn = sqlite3.connect(f"file:{db_path.as_posix()}?mode=ro", uri=True)
cursor = conn.cursor()

def print_table_info(table_name):
    print(f"\n=================== TABLE: {table_name} ===================")
    cursor.execute(f"PRAGMA table_info({table_name})")
    cols = [col[1] for col in cursor.fetchall()]
    print(f"Columns: {cols}")
    count = cursor.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()[0]
    print(f"Row count: {count}")
    if count > 0:
        df = pd.read_sql_query(f"SELECT * FROM {table_name} LIMIT 5", conn)
        print("Sample data:")
        print(df)

# Check schemas of key tables
for t in [
    'trades',
    'signals',
    'msnr_candidates',
    'msnr_candidate_transitions',
    'msnr_candidate_outcomes',
    'msnr_model_registry',
    'strategy_runtime_preferences',
    'instrument_selection_profile_preferences',
    'worker_runtime_states'
]:
    print_table_info(t)

conn.close()
