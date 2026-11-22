import re

files = [
    "app/main.py",
    "config/ict_instrument_policy.py",
    "dashboard/realtime_dashboard.py"
]

for fp in files:
    with open(fp, "r", encoding="utf-8") as f:
        lines = f.readlines()
    print(f"\n=== {fp} ===")
    for i, l in enumerate(lines, 1):
        if any(w in l for w in ["FOREX_SNR", "COMMODITIES_SNR", "MALAYSIAN_SNR"]):
            if any(k in l for k in ["FULL_MULTI_BOT_PROFILES", "profileTab", "_WORKER_PROFILE_META", "ICT_POLICY_PROFILES", "activeProfile ==="]):
                print(f"  {i}: {l.strip()[:110]}")
