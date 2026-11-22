import sqlite3
import json
import os
from datetime import datetime

DB_PATHS = [
    r"C:\Users\sebas\AppData\Local\BlackDaemonFx\trading_bot.sqlite3",
    r"C:\TradingBoot\smc_synthetic_bot\storage\trading_bot.sqlite3",
    r"C:\TradingBoot\smc_synthetic_bot\database\trading_bot.sqlite3"
]

ACTIVE_INDICESB_SNR = sorted([
    "Germany 40", "US Tech 100", "Wall Street 30"
])

now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

for db_path in DB_PATHS:
    if not os.path.exists(db_path):
        continue
    
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    
    cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='instrument_selection_profile_preferences'")
    if cur.fetchone():
        for src in ("DEMO", "LIVE"):
            cur.execute("SELECT id FROM instrument_selection_profile_preferences WHERE source = ? AND selection_profile = 'INDICESB_SNR'", (src,))
            row = cur.fetchone()
            if row:
                cur.execute("""
                    UPDATE instrument_selection_profile_preferences 
                    SET selected_symbols_json = ?, updated_at = ? 
                    WHERE id = ?
                """, (json.dumps(ACTIVE_INDICESB_SNR), now_str, row[0]))
            else:
                cur.execute("""
                    INSERT INTO instrument_selection_profile_preferences 
                    (source, selection_profile, selected_symbols_json, version, updated_at) 
                    VALUES (?, 'INDICESB_SNR', ?, 1, ?)
                """, (src, json.dumps(ACTIVE_INDICESB_SNR), now_str))
        conn.commit()
    conn.close()

print("INDICESB_SNR successfully inserted/updated in all databases!")
