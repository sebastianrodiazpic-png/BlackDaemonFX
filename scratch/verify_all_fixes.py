import sys
sys.path.insert(0, ".")
from config.ict_instrument_policy import ict_active_symbols
from dashboard.realtime_dashboard import RealtimeDashboardService

print("--- TESTING ICT ACTIVE SYMBOLS ---")
active_ict = set(ict_active_symbols("ICT"))
print("Active ICT count:", len(active_ict))
print("Active ICT:", active_ict)

assert "XAGUSD" not in active_ict, "XAGUSD must be pruned from ICT"
assert "ETHUSD" not in active_ict, "ETHUSD must be pruned from ICT"
assert "XAUEUR" not in active_ict, "XAUEUR must be pruned from ICT"
assert "US SP 500" not in active_ict, "US SP 500 must be pruned from ICT"
assert "XRPUSD" not in active_ict, "XRPUSD must be pruned from ICT"

assert "XAUUSD" in active_ict, "XAUUSD must be active in ICT"
assert "BTCUSD" in active_ict, "BTCUSD must be active in ICT"
assert "US Oil" in active_ict, "US Oil must be active in ICT"
assert "UK Brent Oil" in active_ict, "UK Brent Oil must be active in ICT"

print("--- TESTING INDICESB_SNR ACTIVE SYMBOLS ---")
active_indices = set(ict_active_symbols("INDICESB_SNR"))
print("Active INDICESB_SNR count:", len(active_indices))
print("Active INDICESB_SNR:", active_indices)

assert "US SP 500" not in active_indices, "US SP 500 must be pruned from INDICESB_SNR"
assert "Germany 40" in active_indices, "Germany 40 must be active"
assert "US Tech 100" in active_indices, "US Tech 100 must be active"
assert "Wall Street 30" in active_indices, "Wall Street 30 must be active"

print("--- TESTING update_selected_symbols for ICT ---")
srv = RealtimeDashboardService(None)
req_ict = ["BTCUSD", "BTCUSDmicro", "UK Brent Oil", "US Oil", "XAUUSD", "XAUUSDmicro"]
res_ict = srv.update_selected_symbols(req_ict, selection_profile="ICT", allow_selective=True)
print("res_ict ok:", res_ict.get("ok"), "error:", res_ict.get("error"))
assert res_ict.get("ok") is True, f"ICT update failed: {res_ict.get('error')}"

print("--- TESTING update_selected_symbols with Volatility 50 (1s) Index (selective) ---")
cur_synths = srv.get_selected_symbols(selection_profile="SYNTHETICS")
test_synths = cur_synths + ["Volatility 50 (1s) Index"]
res_synths = srv.update_selected_symbols(test_synths, selection_profile="SYNTHETICS", allow_selective=True)
print("res_synths ok:", res_synths.get("ok"), "error:", res_synths.get("error"))
assert res_synths.get("ok") is True, f"SYNTHETICS update failed: {res_synths.get('error')}"
assert "Volatility 50 (1s) Index" in res_synths.get("selected_symbols", []), "Volatility 50 (1s) Index must be kept when allow_selective=True"

print("ALL VERIFICATIONS PASSED SUCCESSFULLY!")
