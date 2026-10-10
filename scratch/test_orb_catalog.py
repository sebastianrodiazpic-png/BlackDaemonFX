import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from brokers.mt5_connector import MT5Connector
from brokers.mt5_data import MT5DataProvider
from strategy.orb.new_york_orb import discover_orb_symbols, classify_orb_market
from dashboard.realtime_dashboard import (
    _selection_profile_for_category,
    _CATEGORY_LABELS,
    DEFAULT_PRIORITIZED_SYMBOLS,
    PRUNED_INSTRUMENTS_INFO,
    RealtimeDashboardService
)
from database.repository import TradingRepository

connector = MT5Connector()
provider = MT5DataProvider(connector)
provider.connect()

symbols = discover_orb_symbols(provider)
print("=== DISCOVERED ORB SYMBOLS FROM MT5 ===")
for s in symbols:
    print(f"  Symbol: {s:15} | Market: {classify_orb_market(s)}")

categorized = {}
for s in symbols:
    market = classify_orb_market(s) or "ORB"
    categorized.setdefault(f"orb_ny_{str(market).lower()}", []).append(s)

print("\n=== CATEGORIZED ORB GROUPS ===")
for cat, sym_list in categorized.items():
    label = _CATEGORY_LABELS.get(cat, cat.replace("_", " ").title())
    profile = _selection_profile_for_category(cat)
    print(f"  Category: {cat:25} | Label: {label:25} | Profile: {profile:10} | Symbols: {sym_list}")

repo = TradingRepository()
db_orb = repo.latest_instrument_selection_profile("ORB")
print("\n=== PERSISTED ORB PROFILE IN DB ===")
print("  Active symbols in DB:", db_orb)

print("\n=== PRIORITIZED SYMBOLS IN DASHBOARD ===")
print("  ORB prioritized:", DEFAULT_PRIORITIZED_SYMBOLS.get("ORB"))

provider.disconnect()
