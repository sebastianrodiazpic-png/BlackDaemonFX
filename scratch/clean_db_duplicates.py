import sys, os
sys.path.insert(0, os.path.abspath("."))
import sqlite3
from database.database import resolve_db_path

db_path = resolve_db_path()
conn = sqlite3.connect(db_path)
c = conn.cursor()
c.execute("DELETE FROM worker_runtime_states WHERE bot_profile IN ('COMMODITIES', 'INDICES')")
conn.commit()
print("Rows deleted:", c.rowcount)
conn.close()
