import sys
sys.path.insert(0, ".")
import time
import os
from database.repository import TradingRepository
from dashboard.realtime_dashboard import RealtimeDashboardService

repo = TradingRepository()
dash = RealtimeDashboardService(repository=repo, host="127.0.0.1", port=8765)

def time_call(name, fn):
    t0 = time.time()
    res = fn()
    dt = time.time() - t0
    print(f"{name:<40}: {dt*1000:>8.2f} ms")
    return res

print("Timing snapshot internal components:")
time_call("_refresh_selection_profiles_from_db_locked", dash._refresh_selection_profiles_from_db_locked)
time_call("_refresh_open_positions_locked", dash._refresh_open_positions_locked)
time_call("_refresh_account_locked", dash._refresh_account_locked)

from dashboard.realtime_dashboard import quarantine_snapshot, smc_trial_snapshot, learning_snapshot
time_call("quarantine_snapshot", quarantine_snapshot)
time_call("smc_trial_snapshot", smc_trial_snapshot)
time_call("learning_snapshot", learning_snapshot)

from dashboard.orb_audit import snapshot as orb_audit_snapshot
time_call("orb_audit_snapshot", orb_audit_snapshot)

from strategy.execution.forex_spread_guard import snapshot as forex_spread_snapshot
time_call("forex_spread_snapshot", forex_spread_snapshot)

time_call("full snapshot()", dash.snapshot)
