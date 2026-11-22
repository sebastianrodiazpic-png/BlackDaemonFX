import json, os

print("=== storage/dashboard/last_state.json KEYS ===")
with open("storage/dashboard/last_state.json", "r", encoding="utf-8") as f:
    state = json.load(f)
print("Top-level keys:", list(state.keys()))

for k in ["account", "active_positions", "open_positions", "positions", "workers", "strategies", "stats", "recent_trades", "events"]:
    if k in state:
        val = state[k]
        if isinstance(val, list):
            print(f"Key '{k}': list with {len(val)} items")
            if len(val) > 0:
                print(f"  first item sample: {str(val[0])[:200]}")
        elif isinstance(val, dict):
            print(f"Key '{k}': dict with keys {list(val.keys())[:10]}")
        else:
            print(f"Key '{k}': {val}")

print("\n=== storage/learning_audit/DEMO_ICT.json ===")
with open("storage/learning_audit/DEMO_ICT.json", "r", encoding="utf-8") as f:
    ict_audit = json.load(f)
print("ICT audit keys:", list(ict_audit.keys()) if isinstance(ict_audit, dict) else f"type {type(ict_audit)}")
if isinstance(ict_audit, dict):
    for k, v in list(ict_audit.items())[:5]:
        print(f"  {k}: {str(v)[:150]}")
