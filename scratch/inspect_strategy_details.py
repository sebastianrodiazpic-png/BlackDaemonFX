import sys
from pathlib import Path
import sqlite3
import json

ROOT = Path("c:/TradingBoot/smc_synthetic_bot")
sys.path.insert(0, str(ROOT))

db_path = r"C:\Users\sebas\AppData\Local\BlackDaemonFx\trading_bot.sqlite3"
conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
conn.row_factory = sqlite3.Row
cur = conn.cursor()

print("--- 1. PROFILES IN SQLITE ---")
profiles = cur.execute("SELECT selection_profile, selected_symbols_json FROM instrument_selection_profile_preferences").fetchall()
for p in profiles:
    syms = json.loads(p['selected_symbols_json']) if p['selected_symbols_json'] else []
    print(f"Profile: {p['selection_profile']:15s} | Count: {len(syms):2d} | Symbols: {syms}")

print("\n--- 2. ORB ASSET PROFILES IN CODE ---")
from strategy.orb.new_york_orb import ORBConfig
orb_cfg = ORBConfig()
print("ORB asset_profiles keys:", list(orb_cfg.asset_profiles.keys()))
for k, v in orb_cfg.asset_profiles.items():
    if isinstance(v, dict):
        print(f"  {k}: enabled={v.get('enabled')}, session_open={v.get('opening_hour')}:{v.get('opening_minute')}, close={v.get('session_close_hour')}:{v.get('session_close_minute')}, cutoff={v.get('entry_cutoff_hour')}:{v.get('entry_cutoff_minute')}, range_min={v.get('opening_range_minutes')}")
    else:
        print(f"  {k}: {v}")


print("\n--- 3. GOLD QUARTERS DEFINITION ---")
import inspect
from strategy.gold_quarters import GoldQuarterStrategy
print("GoldQuarterStrategy doc / init args:")
print(inspect.signature(GoldQuarterStrategy.__init__))
# View source lines of gold_quarters.py
src = Path("strategy/gold_quarters.py").read_text(encoding="utf-8")
print(f"strategy/gold_quarters.py lines: {len(src.splitlines())}")
print("First 40 lines of gold_quarters.py:")
for line in src.splitlines()[:40]:
    print(" ", line)

print("\n--- 4. MALAYSIAN SNR UNIVERSE ---")
import strategy.malaysian_snr.universe as msnr_u
print("MSNR CATALOG_SYMBOLS count:", len(msnr_u.CATALOG_SYMBOLS))
print("MSNR CATALOG_SYMBOLS:", msnr_u.CATALOG_SYMBOLS)
print("MSNR FAMILIES:", msnr_u.FAMILIES.keys())

print("\n--- 5. ICT UNIVERSE & CONFIG ---")
from strategy.ict.config import ICTSabriMalleConfig
from strategy.ict.ict_strategy import ICTSabriMalleStrategy
ict_cfg = ICTSabriMalleConfig()
print("ICTSabriMalleConfig fields:")
for f in dir(ict_cfg):
    if not f.startswith('_') and not callable(getattr(ict_cfg, f)):
        print(f"  {f}: {getattr(ict_cfg, f)}")

print("\n--- 6. HISTORICAL DATA FILES IN STORAGE ---")
storage_path = ROOT / "storage"
if storage_path.exists():
    for p in storage_path.rglob("*"):
        if p.is_file() and p.suffix in [".csv", ".parquet", ".json", ".pkl"]:
            print(f"  {p.relative_to(ROOT)} ({p.stat().st_size / 1024:.1f} KB)")
