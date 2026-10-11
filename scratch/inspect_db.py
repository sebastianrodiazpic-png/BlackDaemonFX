import sys
import os
sys.path.insert(0, os.path.abspath("."))
import sqlite3
import json
from database.database import resolve_db_path

c = sqlite3.connect(resolve_db_path()).cursor()

# Get the last cycle number for Malaysian SNR
r = c.execute("SELECT cycle_number, pid, status, symbols_processed, symbols_total, current_symbol FROM worker_runtime_states WHERE bot_profile='MALAYSIAN_SNR'").fetchone()
print("Worker state:", r)

# Get all SYMBOL_PROCESS_RESULT events for Malaysian SNR in recent events
rows = c.execute("""
    SELECT id, cycle_number, instrument, action, reason, 
           json_extract(payload_json, '$.index'), 
           json_extract(payload_json, '$.total'),
           event_time
    FROM daemon_audit_events
    WHERE event_type='SYMBOL_PROCESS_RESULT' 
      AND (json_extract(payload_json, '$.result.strategy_name')='MALAYSIAN_SNR' 
           OR json_extract(payload_json, '$.result._bot_profile')='MALAYSIAN_SNR'
           OR json_extract(payload_json, '$.result.strategy_name')='Malaysian SNR')
    ORDER BY id DESC LIMIT 30
""").fetchall()

print(f"\nRecent events ({len(rows)}):")
for row in rows:
    print(row)

# Let's inspect the symbols in a full cycle of Malaysian SNR
if rows:
    cycle = rows[0][1]
    cycle_rows = c.execute("""
        SELECT json_extract(payload_json, '$.index'), instrument, action, reason
        FROM daemon_audit_events
        WHERE event_type='SYMBOL_PROCESS_RESULT'
          AND cycle_number=?
          AND (json_extract(payload_json, '$.result.strategy_name')='MALAYSIAN_SNR' 
               OR json_extract(payload_json, '$.result._bot_profile')='MALAYSIAN_SNR'
               OR json_extract(payload_json, '$.result.strategy_name')='Malaysian SNR')
        ORDER BY json_extract(payload_json, '$.index')
    """, (cycle,)).fetchall()
    print(f"\nCycle {cycle} symbols ({len(cycle_rows)}):")
    for cr in cycle_rows:
        print(cr)
