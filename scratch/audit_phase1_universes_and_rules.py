import sys
import sqlite3
import json
from pathlib import Path
import MetaTrader5 as mt5

ROOT = Path("c:/TradingBoot/smc_synthetic_bot")
sys.path.insert(0, str(ROOT))

print("=================================================================")
print("PHASE 1: FORENSIC AUDIT OF UNIVERSES, SYMBOLS, AND DATABASE")
print("=================================================================")

# 1. SQLite Database Audit
db_path = r"C:\Users\sebas\AppData\Local\BlackDaemonFx\trading_bot.sqlite3"
conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
conn.row_factory = sqlite3.Row
cur = conn.cursor()

print("\n--- 1.1 Profile Preferences in SQLite ---")
profiles = cur.execute("SELECT selection_profile, selected_symbols_json FROM instrument_selection_profile_preferences").fetchall()
db_profiles = {}
for p in profiles:
    prof_name = p['selection_profile']
    syms = json.loads(p['selected_symbols_json']) if p['selected_symbols_json'] else []
    db_profiles[prof_name] = syms
    print(f"Profile: {prof_name:18s} | Count: {len(syms):2d} | Symbols: {syms}")

# 2. Malaysian SNR Catalog in Code
print("\n--- 1.2 Malaysian SNR in Code ---")
import strategy.malaysian_snr.universe as msnr_u
catalog_syms = msnr_u.CATALOG_SYMBOLS
print(f"Malaysian SNR CATALOG_SYMBOLS Count: {len(catalog_syms)}")
print(f"Catalog Symbols: {catalog_syms}")
enabled_msnr_db = db_profiles.get("MALAYSIAN_SNR", [])
print(f"Malaysian SNR Enabled in SQLite Count: {len(enabled_msnr_db)}")
print(f"Enabled in SQLite: {enabled_msnr_db}")

# 3. ICT Sabri Malle in Code & DB
print("\n--- 1.3 ICT Sabri Malle in Code & DB ---")
from strategy.ict.config import ICTSabriMalleConfig
ict_cfg = ICTSabriMalleConfig()
enabled_ict_db = db_profiles.get("ICT", [])
print(f"ICT Enabled in SQLite Count: {len(enabled_ict_db)}")
print(f"Enabled in SQLite: {enabled_ict_db}")

# 4. ORB in Code & DB
print("\n--- 1.4 New York ORB in Code & DB ---")
from strategy.orb.new_york_orb import ORBConfig, classify_orb_market
orb_cfg = ORBConfig()
orb_code_profiles = list(orb_cfg.asset_profiles.keys())
print(f"ORB asset_profiles in Code Count: {len(orb_code_profiles)}")
print(f"ORB asset_profiles in Code: {orb_code_profiles}")
enabled_orb_db = db_profiles.get("ORB", [])
print(f"ORB Enabled in SQLite Count: {len(enabled_orb_db)}")
print(f"Enabled in SQLite: {enabled_orb_db}")

# 5. Gold Quarters in Code & DB
print("\n--- 1.5 Gold Quarters in Code & DB ---")
import strategy.gold_quarters as gq_mod
from strategy.orb.new_york_orb import is_orb_gold_symbol
enabled_gold_db = db_profiles.get("GOLD", [])
print(f"GOLD Profile Enabled in SQLite Count: {len(enabled_gold_db)}")
print(f"Enabled in SQLite: {enabled_gold_db}")
print(f"is_orb_gold_symbol tests:")
for s in ['XAUUSD', 'XAUUSDmicro', 'microXAUUSD', 'XAGUSD', 'EURUSD', 'Step Index']:
    print(f"  {s:15s} -> is_orb_gold_symbol: {is_orb_gold_symbol(s)}")

# 6. Broker MT5 Symbols check
print("\n--- 1.6 Broker MT5 Available Symbols ---")
if mt5.initialize():
    all_mt5_symbols = [s.name for s in mt5.symbols_get()]
    print(f"Total symbols published by Broker in MT5: {len(all_mt5_symbols)}")
    print("Sample Broker symbols:", all_mt5_symbols[:20])
    
    # Check coverage of each profile in broker
    print("\nBroker Coverage Check:")
    for prof, syms in [("MSNR", enabled_msnr_db), ("ICT", enabled_ict_db), ("ORB", enabled_orb_db), ("GOLD", enabled_gold_db)]:
        present = [s for s in syms if s in all_mt5_symbols]
        missing = [s for s in syms if s not in all_mt5_symbols]
        print(f"  {prof:5s}: {len(present)}/{len(syms)} present in broker MT5. Missing: {missing}")
    mt5.shutdown()
else:
    print("Could not initialize MT5 to check broker symbols.")
