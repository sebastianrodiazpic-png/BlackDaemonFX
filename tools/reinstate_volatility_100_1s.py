import sys
import os

if sys.path and (sys.path[0].endswith("tools") or sys.path[0].endswith("tools\\") or sys.path[0].endswith("tools/")):
    sys.path.pop(0)

import sqlite3
import json
from datetime import datetime, timezone

SYMBOL_TO_REINSTATE = "Volatility 100 (1s) Index"

SYNTHETIC_PROFILES = {
    "SYNTHETICS",
    "MALAYSIAN_SNR",
    "MSNR",
    "TREND_PULLBACK",
    "ICT"  # ICT synthetic list also contains it
}

DATABASES = [
    "storage/live_trading_bot.sqlite3",
    "storage/trading_bot.sqlite3",
    "database/trading_bot.sqlite3"
]

def reinstate_in_database(db_path: str):
    if not os.path.exists(db_path):
        print(f"Saltando {db_path} (no existe)")
        return
        
    print(f"\n--- Reincorporando {SYMBOL_TO_REINSTATE} en {db_path} ---")
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S.%f")
    
    cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [t[0] for t in cur.fetchall()]
    
    # 1. Update instrument_selection_preferences (Global)
    if 'instrument_selection_preferences' in tables:
        cur.execute("SELECT id, source, version, selected_symbols_json FROM instrument_selection_preferences")
        rows = cur.fetchall()
        for r_id, src, ver, syms_json in rows:
            syms = json.loads(syms_json) if syms_json else []
            if SYMBOL_TO_REINSTATE not in syms:
                syms.append(SYMBOL_TO_REINSTATE)
                # Keep stable alphabetical or existing order
                new_ver = (ver or 1) + 1
                cur.execute("""
                    UPDATE instrument_selection_preferences
                    SET selected_symbols_json = ?, version = ?, updated_at = ?
                    WHERE id = ?
                """, (json.dumps(syms, ensure_ascii=False), new_ver, now_str, r_id))
                print(f"  [Global Preferences id={r_id}, src={src}] Version {ver} -> {new_ver}. Agregado {SYMBOL_TO_REINSTATE}. Total ahora: {len(syms)}")
            else:
                print(f"  [Global Preferences id={r_id}, src={src}] Ya contenía {SYMBOL_TO_REINSTATE}.")
                
    # 2. Update instrument_selection_profile_preferences (Per Profile)
    if 'instrument_selection_profile_preferences' in tables:
        cur.execute("SELECT id, source, selection_profile, version, selected_symbols_json FROM instrument_selection_profile_preferences")
        rows = cur.fetchall()
        for r_id, src, prof, ver, syms_json in rows:
            if prof.upper() in SYNTHETIC_PROFILES:
                syms = json.loads(syms_json) if syms_json else []
                if SYMBOL_TO_REINSTATE not in syms:
                    syms.append(SYMBOL_TO_REINSTATE)
                    new_ver = (ver or 1) + 1
                    cur.execute("""
                        UPDATE instrument_selection_profile_preferences
                        SET selected_symbols_json = ?, version = ?, updated_at = ?
                        WHERE id = ?
                    """, (json.dumps(syms, ensure_ascii=False), new_ver, now_str, r_id))
                    print(f"  [Profile Preferences id={r_id}, src={src}, prof={prof}] Version {ver} -> {new_ver}. Agregado {SYMBOL_TO_REINSTATE}. Total ahora: {len(syms)}")
                else:
                    print(f"  [Profile Preferences id={r_id}, src={src}, prof={prof}] Ya contenía {SYMBOL_TO_REINSTATE}.")

    conn.commit()
    conn.close()
    print(f"Reincorporación completada en {db_path}.")

def main():
    for db in DATABASES:
        reinstate_in_database(db)

if __name__ == '__main__':
    main()
