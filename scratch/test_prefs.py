import sys
sys.path.insert(0, '.')
import sqlite3
import json

from config.ict_instrument_policy import POLICY_SELECTION_PROFILES, ict_active_symbols, sanitize_ict_selection
from database.repository import TradingRepository

repo = TradingRepository(db_path='storage/trading_bot.db')
print("=== PREFERENCES IN DATABASE ===")
for p in ['ORB', 'MALAYSIAN_SNR', 'ICT', 'SYNTHETICS', 'FOREX']:
    prefs = repo.get_instrument_selection_profile_preferences(profile=p, source='LIVE')
    print(f"Profile {p} LIVE prefs:", len(prefs or []), prefs[:5] if prefs else None)
    demo_prefs = repo.get_instrument_selection_profile_preferences(profile=p, source='DEMO')
    print(f"Profile {p} DEMO prefs:", len(demo_prefs or []), demo_prefs[:5] if demo_prefs else None)
