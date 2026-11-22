import json
from collections import Counter

with open("storage/dashboard/last_state.json", "r", encoding="utf-8") as f:
    state = json.load(f)

recent = state.get("recent", [])
print(f"Total entries in recent: {len(recent)}")

actions = Counter()
reasons = Counter()
decisions = Counter()
symbols = Counter()
grades = Counter()

for r in recent:
    act = r.get("action")
    actions[act] += 1
    reas = r.get("reason")
    reasons[f"{act} :: {reas}"] += 1
    dec = r.get("decision")
    decisions[dec] += 1
    sym = r.get("symbol")
    symbols[sym] += 1
    gr = r.get("grade")
    grades[gr] += 1

print("\n--- ACTIONS ---")
for k, v in actions.most_common(15):
    print(f"  {k}: {v}")

print("\n--- REASONS BREAKDOWN ---")
for k, v in reasons.most_common(20):
    print(f"  {k}: {v}")

print("\n--- DECISIONS ---")
for k, v in decisions.most_common(10):
    print(f"  {k}: {v}")

print("\n--- GRADES ---")
for k, v in grades.most_common(10):
    print(f"  {k}: {v}")

print("\n--- TOP SYMBOLS EVALUATED ---")
for k, v in symbols.most_common(15):
    print(f"  {k}: {v}")
