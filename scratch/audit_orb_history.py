import json
import glob
import os

files = sorted(glob.glob("storage/runtime/orb_audit/*.json"))
print(f"Total audit files: {len(files)}")

for f in files[-10:]:
    fname = os.path.basename(f)
    try:
        with open(f, "r", encoding="utf-8") as fh:
            data = json.load(fh)
        day = data.get("day")
        latest = data.get("latest", {})
        print(f"\n--- Day: {day} ({fname}) ---")
        for sym, details in latest.items():
            action = details.get("action")
            reason = details.get("reason")
            amp = details.get("range_amplitude", {})
            ratio = amp.get("ratio")
            is_valid = amp.get("isValid")
            print(f"  {sym:12s} | Action: {action} | Reason: {reason} | Ratio: {ratio} (valid={is_valid})")
    except Exception as e:
        print(f"Error {fname}: {e}")
