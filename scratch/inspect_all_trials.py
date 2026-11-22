import json
import glob
from pathlib import Path

print("=== ALL TRIAL RUNTIME FILES ===")
for p in glob.glob("storage/runtime/smc_trial/*.json"):
    try:
        with open(p, "r", encoding="utf-8") as f:
            data = json.load(f)
            prof = data.get("profile", p)
            day = data.get("day", "")
            evals = data.get("evaluations", 0)
            counts = data.get("counts", {})
            latest = data.get("latest", {})
            upd = data.get("updated_at", "")
            print(f"Profile: {prof:15} | Day: {day} | Evals: {evals:6} | Updated: {upd}")
            print(f"   Counts: {counts}")
            sample_reasons = {}
            for sym, info in latest.items():
                act = info.get("action", "")
                rsn = info.get("reason", "")
                sample_reasons[sym] = f"{act} -> {rsn}"
            print(f"   Sample latest reasons: {dict(list(sample_reasons.items())[:5])}")
    except Exception as e:
        print(f"Error {p}: {e}")

print("\n=== SPREAD GATES STATUS ===")
for p in glob.glob("storage/runtime/*spread*/*.json"):
    try:
        with open(p, "r", encoding="utf-8") as f:
            data = json.load(f)
            worker = data.get("worker", p)
            upd = data.get("updated_at", "")
            symbols = data.get("symbols", {})
            print(f"Spread Gate: {worker:15} | Updated: {upd} | Symbol count: {len(symbols)}")
    except Exception as e:
        print(f"Error {p}: {e}")
