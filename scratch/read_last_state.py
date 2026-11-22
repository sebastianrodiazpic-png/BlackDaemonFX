import json

with open("storage/dashboard/last_state.json", "r", encoding="utf-8") as f:
    state = json.load(f)

print("STATUS:", state.get("status"))
print("CONNECTION_MODE:", state.get("connection_mode"))
print("CYCLE:", state.get("cycle"))
print("DATA FRESHNESS:", state.get("data_freshness"))
print("UPDATED AT:", state.get("updated_at"))
print("SYMBOLS PROCESSED:", state.get("symbols_processed"), "of", state.get("symbols_total"))
print("POSITION HEALTH SUMMARY:", state.get("position_health_summary"))
print("RECENT:", state.get("recent"))
