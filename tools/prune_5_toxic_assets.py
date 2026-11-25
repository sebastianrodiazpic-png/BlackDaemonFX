import sys
import os

# Fix shadowing of standard library 'operator' by local tools/operator directory
if sys.path and (sys.path[0].endswith("tools") or sys.path[0].endswith("tools\\") or sys.path[0].endswith("tools/")):
    sys.path.pop(0)

import sqlite3
import json
from datetime import datetime, timezone

TOXIC_SYMBOLS = {
    'Crash 300 Index',
    'USDJPY',
    'USDJPYmicro',
    'EURUSD',
    'EURUSDmicro',
    'US SP 500'
}

PRESERVED_SYMBOLS = {
    'Step Index 200',
    'Volatility 25 Index',
    'Volatility 100 (1s) Index'
}

DATABASES = [
    'storage/live_trading_bot.sqlite3',
    'storage/trading_bot.sqlite3',
    'database/trading_bot.sqlite3'
]

def prune_database(db_path: str):
    if not os.path.exists(db_path):
        print(f"Skipping {db_path} (does not exist)")
        return
        
    print(f"\nProcesando poda en: {db_path}")
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S.%f")
    
    cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [t[0] for t in cur.fetchall()]
    
    # 1. Prune instrument_selection_preferences (Global)
    if 'instrument_selection_preferences' in tables:
        cur.execute("SELECT id, source, version, selected_symbols_json FROM instrument_selection_preferences")
        rows = cur.fetchall()
        for r_id, src, ver, syms_json in rows:
            syms = json.loads(syms_json) if syms_json else []
            pruned_syms = [s for s in syms if s not in TOXIC_SYMBOLS]
            removed = [s for s in syms if s in TOXIC_SYMBOLS]
            new_ver = (ver or 1) + 1
            
            cur.execute("""
                UPDATE instrument_selection_preferences
                SET selected_symbols_json = ?, version = ?, updated_at = ?
                WHERE id = ?
            """, (json.dumps(pruned_syms, ensure_ascii=False), new_ver, now_str, r_id))
            print(f"  [Global Preferences id={r_id}, src={src}] Version {ver} -> {new_ver}. Removidos {len(removed)}: {removed}. Total ahora: {len(pruned_syms)}")
            
    # 2. Prune instrument_selection_profile_preferences (Per Profile)
    if 'instrument_selection_profile_preferences' in tables:
        cur.execute("SELECT id, source, selection_profile, version, selected_symbols_json FROM instrument_selection_profile_preferences")
        rows = cur.fetchall()
        for r_id, src, prof, ver, syms_json in rows:
            syms = json.loads(syms_json) if syms_json else []
            pruned_syms = [s for s in syms if s not in TOXIC_SYMBOLS]
            removed = [s for s in syms if s in TOXIC_SYMBOLS]
            if removed:
                new_ver = (ver or 1) + 1
                cur.execute("""
                    UPDATE instrument_selection_profile_preferences
                    SET selected_symbols_json = ?, version = ?, updated_at = ?
                    WHERE id = ?
                """, (json.dumps(pruned_syms, ensure_ascii=False), new_ver, now_str, r_id))
                print(f"  [Profile Preferences id={r_id}, src={src}, prof={prof}] Version {ver} -> {new_ver}. Removidos {len(removed)}: {removed}. Total ahora: {len(pruned_syms)}")
                
    conn.commit()
    conn.close()
    print(f"Poda completada exitosamente en {db_path}.")

def main():
    for db in DATABASES:
        prune_database(db)

if __name__ == '__main__':
    main()
