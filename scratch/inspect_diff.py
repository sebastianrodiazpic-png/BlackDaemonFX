import sys
import os
sys.path.insert(0, os.path.abspath("."))
import sqlite3
import json
from database.database import resolve_db_path

c = sqlite3.connect(resolve_db_path()).cursor()

rows = c.execute("""
    SELECT json_extract(payload_json, '$.index') as idx, instrument
    FROM daemon_audit_events
    WHERE event_type='SYMBOL_PROCESS_RESULT' 
      AND (json_extract(payload_json, '$.result.strategy_name')='MALAYSIAN_SNR' 
           OR json_extract(payload_json, '$.result._bot_profile')='MALAYSIAN_SNR')
      AND id >= 2303000
    GROUP BY idx
    ORDER BY idx
""").fetchall()

print("The 20 symbols processed by Malaysian SNR:")
for r in rows:
    print(f"Index {r[0]}: {r[1]}")

# Now let's compare with the 23 symbols in preferences and config:
pref_row = c.execute("SELECT selected_symbols_json FROM instrument_selection_profile_preferences WHERE source='DEMO' AND selection_profile='MALAYSIAN_SNR'").fetchone()
pref_syms = json.loads(pref_row[0]) if pref_row else []
print(f"\nTotal selected in DEMO preferences: {len(pref_syms)}")
print("Preference symbols:", pref_syms)

processed_syms = [r[1] for r in rows]
missing_from_worker = set(pref_syms) - set(processed_syms)
print(f"\nMissing from worker ({len(missing_from_worker)}):", missing_from_worker)
