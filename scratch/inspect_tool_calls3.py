# -*- coding: utf-8 -*-
import json

with open("C:/Users/sebas/.gemini/antigravity/brain/a78072a2-83cd-4242-9935-27e1da602ecb/.system_generated/logs/transcript.jsonl", "r", encoding="utf-8") as f:
    lines = f.readlines()

for idx in range(1400, 1650):
    l = lines[idx]
    if "write_file" in l or "strategy_bases" in l:
        try:
            obj = json.loads(l)
            calls = obj.get("tool_calls", [])
            for c in calls:
                p = c.get("args", {}).get("Path", "") or c.get("args", {}).get("CommandLine", "")
                if p:
                    print(f"Step {idx}: {c.get('name')} -> {p}")
        except Exception:
            pass
