import json

for path in [
    "storage/runtime/smc_trial/ICT.json",
    "storage/runtime/smc_trial/INDICESB_SNR.json",
    "storage/runtime/smc_trial/ORB.json",
    "storage/runtime/smc_telemetry/ICT_22940.json",
    "storage/runtime/smc_telemetry/INDICESB_SNR_33308.json",
]:
    print("=" * 60)
    print("PATH:", path)
    try:
        with open(path, "r", encoding="utf-8") as f:
            d = json.load(f)
            print(json.dumps(d, indent=2))
    except Exception as e:
        print("Error:", e)
