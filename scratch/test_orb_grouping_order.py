import sys
sys.path.insert(0, ".")
from dashboard.realtime_dashboard import RealtimeDashboardService, _CATEGORY_LABELS, _ORB_CATEGORY_ORDER

svc = RealtimeDashboardService(repository=None)
cat = {
    "orb_ny_audusd": ["AUDUSD", "AUDUSDmicro"],
    "orb_ny_xauusd": ["XAUUSD", "XAUUSDmicro", "XAUEUR", "XAUEURmicro"],
    "orb_ny_xagusd": ["XAGUSD", "XAGUSDmicro"],
    "orb_ny_us_oil": ["US Oil"],
    "orb_ny_btcusd": ["BTCUSD", "BTCUSDmicro"],
    "orb_ny_ethusd": ["ETHUSD", "ETHUSDmicro"],
    "orb_ny_eurusd": ["EURUSD", "EURUSDmicro"],
    "orb_ny_wall_street_30": ["Wall Street 30"],
}
svc.set_instrument_catalog(cat)
orb_cards = [g for g in svc._state["instrument_catalog"] if g["selection_profile"] == "ORB"]
print("ORB Cards order:")
for c in orb_cards:
    print(f"  {c['label']}: {c['symbols']}")
