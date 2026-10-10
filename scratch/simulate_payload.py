import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from brokers.mt5_connector import MT5Connector
from brokers.mt5_data import MT5DataProvider
from strategy.orb.new_york_orb import discover_orb_symbols, classify_orb_market
from dashboard.realtime_dashboard import (
    RealtimeDashboardService,
    _selection_profile_for_category,
    _CATEGORY_LABELS,
    DEFAULT_PRIORITIZED_SYMBOLS,
    PRUNED_INSTRUMENTS_INFO
)
from database.repository import TradingRepository

connector = MT5Connector()
provider = MT5DataProvider(connector)
provider.connect()

symbols = discover_orb_symbols(provider)
categorized = {}
for s in symbols:
    market = classify_orb_market(s) or "ORB"
    categorized.setdefault(f"orb_ny_{str(market).lower()}", []).append(s)

repo = TradingRepository()
service = RealtimeDashboardService(repository=repo)
service.set_instrument_catalog(categorized)

payload = service._cached_instruments_payload(force=True)

print("=== INSTRUMENT CATALOG IN PAYLOAD ===")
for cat in payload["instrument_catalog"]:
    if cat.get("selection_profile") == "ORB":
        print(f"Category: {cat['category']} | Label: {cat['label']} | Symbols: {cat['symbols']}")

orb_chosen = set(payload["selection_profiles"].get("ORB", []))
orb_prioritized = set(payload["prioritized_symbols"].get("ORB", []))
orb_pruned_info = payload["pruned_instruments_by_profile"].get("ORB", {})

print("\n=== VERIFYING EACH DISCOVERED SYMBOL IN UI ===")
for cat in payload["instrument_catalog"]:
    if cat.get("selection_profile") == "ORB":
        for sym in cat["symbols"]:
            is_checked = sym in orb_chosen
            is_prioritized = sym in orb_prioritized
            is_pruned = not is_prioritized and (bool(orb_pruned_info.get(sym)) or (len(orb_prioritized) > 0 and not is_prioritized))
            badge = "DESCARTADO (PODA)" if is_pruned else "PRIORIZADO"
            print(f"Symbol: {sym:15} | Active/Checked: {str(is_checked):5} | Prioritized: {str(is_prioritized):5} | Pruned: {str(is_pruned):5} | Badge: {badge}")

provider.disconnect()
