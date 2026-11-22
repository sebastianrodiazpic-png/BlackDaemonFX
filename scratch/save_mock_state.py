import sys
sys.path.insert(0, '.')
import json

from dashboard.realtime_dashboard import RealtimeDashboardService

dash = RealtimeDashboardService()
payload = dash._cached_instruments_payload(force=True)

with open('scratch/mock_state.json', 'w', encoding='utf-8') as f:
    json.dump(payload, f, ensure_ascii=False, indent=2)

print("Saved scratch/mock_state.json with keys:", list(payload.keys()))
