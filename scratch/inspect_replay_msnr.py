import json

with open("storage/analysis/replay_before_after_full_212_20261105.json", "r", encoding="utf-8") as f:
    data = json.load(f)

for item in data:
    strat = item.get("strategy") or ""
    sym = item.get("symbol") or ""
    if "malaysian" in strat.lower() or "msnr" in strat.lower():
        if any(k.lower() in sym.lower() for k in ["usdchf", "audcad", "germany", "audusd", "ger40", "vol over"]):
            print(f"=== {sym} ===")
            print(json.dumps(item, indent=2))
