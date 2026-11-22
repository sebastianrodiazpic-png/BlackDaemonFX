import sys
sys.path.insert(0, '.')

from dashboard.realtime_dashboard import RealtimeDashboardService, DEFAULT_PRIORITIZED_SYMBOLS

print("Testing _refresh_selection_profiles_from_db_locked behavior...")
service = RealtimeDashboardService()
with service._lock:
    service._refresh_selection_profiles_from_db_locked()
    cur_synth = list(service._state.get("selection_profiles", {}).get("SYNTHETICS", []))
    print(f"Current SYNTHETICS count: {len(cur_synth)}")
    print(f"Is 'Volatility 50 (1s) Index' in SYNTHETICS? {'Volatility 50 (1s) Index' in cur_synth}")

# Now let's simulate unchecking Volatility 50 (1s) Index
new_selection = [s for s in cur_synth if s != "Volatility 50 (1s) Index"]
print(f"\nSaving selection WITHOUT Volatility 50 (1s) Index ({len(new_selection)} symbols)...")
res = service.update_selected_symbols(new_selection, selection_profile="SYNTHETICS", allow_selective=True)
print("update_selected_symbols result:", res.get("ok"), res.get("message"))

# Now let's simulate the immediate load() call that happens after save()
with service._lock:
    service._refresh_selection_profiles_from_db_locked()
    after_load = list(service._state.get("selection_profiles", {}).get("SYNTHETICS", []))
    print(f"\nAfter _refresh_selection_profiles_from_db_locked:")
    print(f"Is 'Volatility 50 (1s) Index' BACK in SYNTHETICS? {'Volatility 50 (1s) Index' in after_load}")
