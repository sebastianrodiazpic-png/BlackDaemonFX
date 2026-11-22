# -*- coding: utf-8 -*-
with open("C:/Users/sebas/.gemini/antigravity/brain/a78072a2-83cd-4242-9935-27e1da602ecb/.system_generated/logs/transcript.jsonl", "r", encoding="utf-8") as f:
    lines = f.readlines()

import json
for step_idx in [958, 960, 962]:
    obj = json.loads(lines[step_idx])
    print(f"--- STEP {step_idx} ---")
    for c in obj.get("tool_calls", []):
        print("Name:", c.get("name"))
        args = c.get("args", {})
        if "CommandLine" in args:
            print("Command:", args["CommandLine"][:400])
        if "Content" in args:
            print("Content:", args["Content"][:1500])
