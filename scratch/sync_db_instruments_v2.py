import sqlite3
import json
import shutil
import os
from datetime import datetime

DB_PATHS = [
    r"C:\Users\sebas\AppData\Local\BlackDaemonFx\trading_bot.sqlite3",
    r"C:\TradingBoot\smc_synthetic_bot\storage\trading_bot.sqlite3",
    r"C:\TradingBoot\smc_synthetic_bot\database\trading_bot.sqlite3"
]

ACTIVE_SYNTHETICS = sorted([
    # Jump (5 activos 100% habilitados)
    "Jump 10 Index", "Jump 25 Index", "Jump 50 Index", "Jump 75 Index", "Jump 100 Index",
    # Boom (5 activos probados)
    "Boom 300 Index", "Boom 500 Index", "Boom 600 Index", "Boom 900 Index", "Boom 1000 Index",
    # Crash (3 activos probados)
    "Crash 500 Index", "Crash 900 Index", "Crash 1000 Index",
    # Volatility estándar (6 activos)
    "Volatility 5 Index", "Volatility 10 Index", "Volatility 50 Index", "Volatility 75 Index",
    "Volatility 90 Index", "Volatility 100 Index",
    # Volatility 1s (10 activos - sin Vol 50 1s)
    "Volatility 5 (1s) Index", "Volatility 10 (1s) Index", "Volatility 15 (1s) Index",
    "Volatility 25 (1s) Index", "Volatility 30 (1s) Index", "Volatility 75 (1s) Index",
    "Volatility 90 (1s) Index", "Volatility 100 (1s) Index", "Volatility 150 (1s) Index",
    "Volatility 250 (1s) Index",
    # Step comprobados (2 activos)
    "Step Index 400", "Step Index 500"
])

print(f"Total active synths defined: {len(ACTIVE_SYNTHETICS)}")

now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

for db_path in DB_PATHS:
    if not os.path.exists(db_path):
        continue
    
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    
    cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='instrument_selection_profile_preferences'")
    if cur.fetchone():
        syms_json = json.dumps(ACTIVE_SYNTHETICS)
        cur.execute("""
            UPDATE instrument_selection_profile_preferences 
            SET selected_symbols_json = ?, updated_at = ? 
            WHERE selection_profile = 'SYNTHETICS'
        """, (syms_json, now_str))
        print(f"[{db_path}] Updated SYNTHETICS to {len(ACTIVE_SYNTHETICS)} symbols. Rows affected: {cur.rowcount}")

        cur.execute("""
            UPDATE instrument_selection_profile_preferences 
            SET selected_symbols_json = ?, updated_at = ? 
            WHERE selection_profile IN ('MALAYSIAN_SNR', 'MSNR')
        """, (syms_json, now_str))
        print(f"[{db_path}] Updated MSNR. Rows affected: {cur.rowcount}")
        
        conn.commit()
    conn.close()

print("All databases successfully updated and verified!")
