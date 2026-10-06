import glob
import os
import json

print("=== REPLAY AUDIT ACROSS ALL WORKERS IN STORAGE/RUNTIME/SMC_TRIAL/REPLAY ===")

for f in sorted(glob.glob("storage/runtime/smc_trial/replay/*.json")):
    worker = os.path.basename(f).replace(".json", "")
    with open(f, "r", encoding="utf-8") as fp:
        try:
            d = json.load(fp)
            vars = d.get("variants", {})
            cands = d.get("candidates", [])
            print(f"\nWorker: {worker} (Total candidates: {len(cands)})")
            for v_name, v_data in vars.items():
                tp = v_data.get("tp", 0)
                sl = v_data.get("sl", 0)
                tot = tp + sl
                wr = (tp / tot * 100) if tot > 0 else 0
                gross_r = v_data.get("gross_r_sum", 0)
                print(f"   Variante: {v_name:40} | TP: {tp:2} | SL: {sl:2} | WR: {wr:5.1f}% | Gross R: {gross_r:+.2f}R")
        except Exception as e:
            print(f"Error reading {f}: {e}")
