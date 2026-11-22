import os

bots = ["forex_1", "forex_5", "ict", "indicesb_snr", "orb"]

for b in bots:
    p = f"storage/logs/bots/{b}.log"
    print("=" * 80)
    print(f"BOT LOG: {b.upper()} ({p})")
    if not os.path.exists(p):
        print("  File not found")
        continue
    with open(p, "r", encoding="utf-8", errors="ignore") as f:
        lines = f.readlines()
        tail = lines[-40:] if len(lines) >= 40 else lines
        for line in tail:
            print(" ", line.strip())
