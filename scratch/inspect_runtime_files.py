import json
import glob
from pathlib import Path

files = [
    "storage/runtime/forex_spread/FOREX_1.json",
    "storage/runtime/forex_spread/FOREX_5.json",
    "storage/runtime/forex_spread/FOREX_2.json",
    "storage/runtime/commodity_spread/ORB.json",
    "storage/runtime/commodity_spread/ICT.json",
    "storage/runtime/index_spread/INDICESB_SNR.json",
    "storage/runtime/index_spread/ICT.json",
    "storage/runtime/smc_trial/FOREX_1.json",
    "storage/runtime/smc_trial/FOREX_5.json",
]

for fp in files:
    p = Path(fp)
    if p.exists():
        print("=" * 60)
        print("FILE:", fp)
        try:
            with open(p, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, dict):
                    # print top keys and preview
                    for k, v in list(data.items())[:10]:
                        if isinstance(v, (dict, list)) and len(str(v)) > 200:
                            print(f"  {k}: {type(v)} (len={len(v)}) -> {str(v)[:150]}...")
                        else:
                            print(f"  {k}: {v}")
                elif isinstance(data, list):
                    print(f"  List of {len(data)} items. Sample: {data[:2]}")
        except Exception as e:
            print("Error reading:", e)

# Also let's check files in storage/runtime/smc_telemetry/
print("=" * 60)
print("SMC TELEMETRY FILES:")
for tp in glob.glob("storage/runtime/smc_telemetry/*.json"):
    print(tp)
    try:
        with open(tp, "r", encoding="utf-8") as f:
            d = json.load(f)
            print("  keys:", list(d.keys())[:8])
            print("  preview:", {k: d[k] for k in list(d.keys())[:5]})
    except Exception as e:
        print("  Error:", e)
