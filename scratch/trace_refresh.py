import sys
sys.path.insert(0, '.')

from dashboard.realtime_dashboard import RealtimeDashboardService
from database.repository import TradingRepository
from database.database import get_session_factory

repo = TradingRepository(get_session_factory())
service = RealtimeDashboardService(repository=repo)

with service._lock:
    persisted = service.repository.latest_instrument_selection_profiles(source="DEMO") or {}
    synth_pref = persisted.get("SYNTHETICS")
    print("persisted.get('SYNTHETICS') is:", synth_pref is not None)
    if synth_pref:
        print("persisted selected_symbols has Vol 50 1s?:", "Volatility 50 (1s) Index" in synth_pref.get("selected_symbols", []))

print("\n--- Testing update_selected_symbols without Volatility 50 (1s) Index ---")
cur_synth = list(synth_pref.get("selected_symbols", [])) if synth_pref else []
new_selection = [s for s in cur_synth if s != "Volatility 50 (1s) Index"]
print(f"Old count: {len(cur_synth)}, New count: {len(new_selection)}")

res = service.update_selected_symbols(new_selection, selection_profile="SYNTHETICS", allow_selective=True)
print("update result:", res.get("ok"), res.get("message"))

with service._lock:
    service._refresh_selection_profiles_from_db_locked()
    after_load = list(service._state.get("selection_profiles", {}).get("SYNTHETICS", []))
    print(f"\nAfter _refresh_selection_profiles_from_db_locked:")
    print(f"Is 'Volatility 50 (1s) Index' BACK in SYNTHETICS? {'Volatility 50 (1s) Index' in after_load}")
    print(f"New SYNTHETICS count: {len(after_load)}")
