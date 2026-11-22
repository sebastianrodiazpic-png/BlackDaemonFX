import sys
sys.path.insert(0, ".")
from dashboard.realtime_dashboard import RealtimeDashboardService

dash = RealtimeDashboardService()
data = dash._cached_instruments_payload(force=True)
workers = data.get("worker_states", [])
print(f"Total workers: {len(workers)}")
for w in workers:
    prof = w.get("bot_profile")
    status = w.get("status")
    action = w.get("last_action")
    reason = w.get("last_reason")
    pid = w.get("pid")
    updated = w.get("updated_at")
    print(f"Worker: {prof:15} | PID: {str(pid):6} | Status: {status:15} | Action: {str(action):20} | Reason: {str(reason)[:40]}")
