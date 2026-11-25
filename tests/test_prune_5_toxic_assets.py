import sqlite3
import json
import os
import pytest

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
    'storage/trading_bot.sqlite3'
]

@pytest.mark.parametrize("db_path", DATABASES)
def test_toxic_symbols_removed_from_preferences(db_path):
    if not os.path.exists(db_path):
        pytest.skip(f"{db_path} does not exist")
        
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    
    cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [t[0] for t in cur.fetchall()]
    
    if 'instrument_selection_preferences' in tables:
        cur.execute("SELECT source, selected_symbols_json FROM instrument_selection_preferences")
        for src, syms_json in cur.fetchall():
            syms = set(json.loads(syms_json) if syms_json else [])
            found_toxic = syms.intersection(TOXIC_SYMBOLS)
            assert not found_toxic, f"Found toxic symbols {found_toxic} in {db_path} ({src})"
            
            # Check preserved symbols
            for p_sym in PRESERVED_SYMBOLS:
                assert p_sym in syms, f"Preserved symbol {p_sym} missing in {db_path} ({src})"
                
    if 'instrument_selection_profile_preferences' in tables:
        cur.execute("SELECT source, selection_profile, selected_symbols_json FROM instrument_selection_profile_preferences")
        for src, prof, syms_json in cur.fetchall():
            syms = set(json.loads(syms_json) if syms_json else [])
            found_toxic = syms.intersection(TOXIC_SYMBOLS)
            assert not found_toxic, f"Found toxic symbols {found_toxic} in {db_path} ({src}, {prof})"
            
    conn.close()
