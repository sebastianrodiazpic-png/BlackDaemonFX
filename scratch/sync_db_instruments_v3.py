import sqlite3
import json
import os
from datetime import datetime

DB_PATHS = [
    r"C:\Users\sebas\AppData\Local\BlackDaemonFx\trading_bot.sqlite3",
    r"C:\TradingBoot\smc_synthetic_bot\storage\trading_bot.sqlite3",
    r"C:\TradingBoot\smc_synthetic_bot\database\trading_bot.sqlite3"
]

ACTIVE_ICT = sorted([
    "BTCUSD", "BTCUSDmicro",
    "XAUUSD", "XAUUSDmicro",
    "US Oil", "UK Brent Oil"
])

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
        # Update ICT
        cur.execute("""
            UPDATE instrument_selection_profile_preferences 
            SET selected_symbols_json = ?, updated_at = ? 
            WHERE selection_profile = 'ICT'
        """, (json.dumps(ACTIVE_ICT), now_str))
        print(f"[{db_path}] Updated ICT to {ACTIVE_ICT}. Rows: {cur.rowcount}")

        # Update INDICESB_SNR
        cur.execute("""
            UPDATE instrument_selection_profile_preferences 
            SET selected_symbols_json = ?, updated_at = ? 
            WHERE selection_profile = 'INDICESB_SNR'
        """, (json.dumps(ACTIVE_INDICESB_SNR), now_str))
        print(f"[{db_path}] Updated INDICESB_SNR to {ACTIVE_INDICESB_SNR}. Rows: {cur.rowcount}")
        
        conn.commit()
    conn.close()

print("All databases successfully synced with pruned ICT & INDICESB_SNR!")
