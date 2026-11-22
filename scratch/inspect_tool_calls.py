# -*- coding: utf-8 -*-
import json

with open("C:/Users/sebas/.gemini/antigravity/brain/a78072a2-83cd-4242-9935-27e1da602ecb/.system_generated/logs/transcript.jsonl", "r", encoding="utf-8") as f:
    lines = f.readlines()

for idx in range(1850, 1950):
    l = lines[idx]
    if "write_file" in l or "edit_file" in l or "apply_" in l or "restore_" in l:
        obj = json.loads(l)
        print(f"Step {idx}: type={obj.get('type')}")
        calls = obj.get("tool_calls", [])
        for c in calls:
            print("  Call:", c.get("name"), c.get("args", {}).get("Path", "") or c.get("args", {}).get("CommandLine", ""))
