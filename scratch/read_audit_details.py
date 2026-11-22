import json

with open("storage/learning_audit/DEMO_ICT.json", "r", encoding="utf-8") as f:
    data = json.load(f)

print("closed_comparison:", data.get("closed_comparison"))
print("trade_eligibility:", data.get("trade_eligibility"))
instruments = data.get("instruments", {})
print("Number of instruments:", len(instruments))
for sym, info in list(instruments.items())[:5]:
    print(f"  {sym}: {info}")
