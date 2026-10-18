import sqlite3
import os
import json
from datetime import datetime, timezone

db = os.path.expanduser('~') + r'\AppData\Local\BlackDaemonFx\trading_bot.sqlite3'
conn = sqlite3.connect(db)
c = conn.cursor()

row = c.execute("SELECT id, selected_symbols_json, version FROM instrument_selection_profile_preferences WHERE selection_profile='MALAYSIAN_SNR' ORDER BY id DESC LIMIT 1").fetchone()
if row:
    _id, raw_json, version = row
    syms = json.loads(raw_json)
    print(f"Current MALAYSIAN_SNR selected count: {len(syms)}")
    print("Contains Crash 300 Index?", 'Crash 300 Index' in syms)
    
    # Prune toxic symbols completely:
    # USDCAD, Crash 300 Index, EURCHF, AUDCHF, CADCHF, EURGBP, US Oil
    toxic_set = {'Crash 300 Index', 'USDCAD', 'EURCHF', 'AUDCHF', 'CADCHF', 'EURGBP', 'US Oil', 'AUDNZD'}
    pruned_syms = [s for s in syms if s not in toxic_set]
    
    print(f"Pruned MALAYSIAN_SNR count: {len(pruned_syms)}")
    
    now_str = datetime.now(timezone.utc).isoformat()
    new_version = (version or 1) + 1
    # Update all MALAYSIAN_SNR rows in instrument_selection_profile_preferences
    c.execute('''
        UPDATE instrument_selection_profile_preferences 
        SET selected_symbols_json = ?, version = ?, updated_at = ?
        WHERE selection_profile = 'MALAYSIAN_SNR'
    ''', (json.dumps(pruned_syms), new_version, now_str))
    conn.commit()
    print("SUCCESS: Updated instrument_selection_profile_preferences for MALAYSIAN_SNR")
