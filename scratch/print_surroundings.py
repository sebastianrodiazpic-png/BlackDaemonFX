with open("storage/logs/bots/orb.log", "r", encoding="utf-8", errors="ignore") as f:
    lines = f.readlines()

for i, l in enumerate(lines[-1500:]):
    if "US SP 500" in l or "US Tech 100" in l:
        actual_idx = len(lines) - 1500 + i
        for j in range(max(0, actual_idx - 1), min(len(lines), actual_idx + 4)):
            print(lines[j].rstrip())
        print("-" * 50)
