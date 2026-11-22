import json

with open("storage/runtime/index_spread/INDICESB_SNR.json", "r") as f:
    d = json.load(f)
    print("INDICESB_SNR symbols & latest samples:")
    for sym, val in d.get("symbols", {}).items():
        samples = val.get("samples", [])
        last_s = samples[-1] if samples else None
        print(f"  {sym}: count={len(samples)}, last={last_s}")

with open("storage/runtime/index_spread/ICT.json", "r") as f:
    d = json.load(f)
    print("ICT indices symbols & latest samples:")
    for sym, val in d.get("symbols", {}).items():
        samples = val.get("samples", [])
        last_s = samples[-1] if samples else None
        print(f"  {sym}: count={len(samples)}, last={last_s}")
