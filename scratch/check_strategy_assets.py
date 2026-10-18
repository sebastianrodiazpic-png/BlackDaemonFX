import sys
from pathlib import Path
import sqlite3
import json

ROOT = Path("c:/TradingBoot/smc_synthetic_bot")
sys.path.insert(0, str(ROOT))

print("=== 1. CHECKING STRATEGY ASSETS IN DATABASE ===")
db_path = r"C:\Users\sebas\AppData\Local\BlackDaemonFx\trading_bot.sqlite3"
conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
conn.row_factory = sqlite3.Row
cur = conn.cursor()

# Check instrument_selection_profile_preferences
print("\n--- Profile Preferences in DB ---")
profiles = cur.execute("SELECT * FROM instrument_selection_profile_preferences").fetchall()
for p in profiles:
    symbols = json.loads(p['selected_symbols_json']) if p['selected_symbols_json'] else []
    print(f"Profile: {p['selection_profile']:20s} | Symbols ({len(symbols)}): {symbols}")

# Check strategy_runtime_preferences
print("\n--- Strategy Runtime Preferences in DB ---")
strat_prefs = cur.execute("SELECT * FROM strategy_runtime_preferences").fetchall()
for sp in strat_prefs:
    print(f"Strategy: {sp['strategy_name']:25s} | Source: {sp['source']:10s} | Settings: {sp['settings_json']}")

print("\n=== 2. CHECKING CODE-LEVEL STRATEGY CONFIGURATIONS ===")
# ORB
from strategy.orb.new_york_orb import ORBConfig, NewYorkORBStrategy
print("\n[ORB Configuration]")
orb_cfg = ORBConfig()
print("  ORB Default Symbols:", orb_cfg.default_symbols if hasattr(orb_cfg, 'default_symbols') else "N/A")
print("  ORB Attributes:", [a for a in dir(orb_cfg) if not a.startswith('_')])

# Gold Quarters
from strategy.gold_quarters import GoldQuarterStrategy
print("\n[Gold Quarters Configuration]")
print("  Gold Quarters Attributes/Methods:", [a for a in dir(GoldQuarterStrategy) if not a.startswith('_')])

# ICT
from strategy.ict.config import ICTSabriMalleConfig
print("\n[ICT Sabri Malle Configuration]")
ict_cfg = ICTSabriMalleConfig()
print("  ICT enabled_symbols:", ict_cfg.enabled_symbols if hasattr(ict_cfg, 'enabled_symbols') else "N/A")

# Malaysian SNR
from strategy.malaysian_snr.config import MalaysianSNRConfig
import strategy.malaysian_snr.universe as msnr_universe
print("\n[Malaysian SNR Configuration]")
msnr_cfg = MalaysianSNRConfig()
print("  MSNR universe attributes:", [a for a in dir(msnr_universe) if not a.startswith('_')])
if hasattr(msnr_universe, 'DEFAULT_SYMBOLS'):
    print("  MSNR DEFAULT_SYMBOLS:", getattr(msnr_universe, 'DEFAULT_SYMBOLS'))
if hasattr(msnr_universe, 'ALL_SYMBOLS'):
    print("  MSNR ALL_SYMBOLS:", getattr(msnr_universe, 'ALL_SYMBOLS'))


