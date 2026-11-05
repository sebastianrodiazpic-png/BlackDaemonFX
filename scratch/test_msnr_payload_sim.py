import sys
sys.path.insert(0, '.')

from dashboard.realtime_dashboard import RealtimeDashboardService, DEFAULT_PRIORITIZED_SYMBOLS
import config.ict_instrument_policy as ip

active = ip.ict_active_symbols("MALAYSIAN_SNR")
print(f"Total Malaysian SNR active symbols in policy: {len(active)}")
print("Active symbols:", sorted(active))

# Simulate payload
dash = RealtimeDashboardService(port=9999)
payload = dash._cached_instruments_payload(force=True)

prioritized_msnr = set((payload.get("prioritized_symbols") or {}).get("MALAYSIAN_SNR") or [])
pruned_msnr = (payload.get("pruned_instruments_by_profile") or {}).get("MALAYSIAN_SNR") or {}

print(f"\nPrioritized MSNR count: {len(prioritized_msnr)}")

# Check key symbols
test_symbols = [
    "Vol over Boom 550", "Vol over Crash 550", "Jump 75 Index", "Step Index 200", 
    "Step Index 400", "Step Index 500", "High Frequency Vol 100 Index", "VolSwitch High Vol Index",
    "Volatility 5 Index", "Volatility 90 Index", "Germany 40", "XAUUSD", "USDJPY", "GBPUSD", "NZDUSD",
    "GBPCAD", "CADCHF", "EURGBP", "GBPCHF", "CADJPY"
]

print("\n--- CHECKING WINNERS (>50% WR) ---")
for s in test_symbols:
    is_prioritized = s in prioritized_msnr
    prune_msg = pruned_msnr.get(s, "")
    is_pruned = not is_prioritized and bool(prune_msg)
    print(f"{s}: Prioritized={is_prioritized}, Pruned={is_pruned}, Warning={repr(prune_msg)}")

print("\n--- CHECKING LOSERS (<=50% WR) ---")
for s in ["Volatility 10 Index", "Volatility 50 (1s) Index", "Crash 900 Index", "Step Index", "Boom 1000 Index", "Jump 50 Index", "GBPJPY"]:
    is_prioritized = s in prioritized_msnr
    prune_msg = pruned_msnr.get(s, "")
    is_pruned = not is_prioritized and (bool(prune_msg) or len(prioritized_msnr) > 0)
    print(f"{s}: Prioritized={is_prioritized}, Pruned={is_pruned}, Warning={repr(prune_msg)}")
