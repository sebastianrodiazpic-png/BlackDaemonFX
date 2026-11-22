with open("storage/logs/bots/orb.log", "r", encoding="utf-8", errors="ignore") as f:
    lines = f.readlines()

capturing = False
current_cycle = ""
target_entries = []

for line in lines:
    if "CICLO #" in line:
        current_cycle = line.strip()
    if any(sym in line for sym in ["US SP 500", "US Tech 100"]):
        target_entries.append((current_cycle, line.strip()))

print(f"Total target lines found: {len(target_entries)}")
for c, l in target_entries[-40:]:
    print(f"{c} | {l}")
