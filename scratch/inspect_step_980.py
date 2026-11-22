# -*- coding: utf-8 -*-
with open("C:/Users/sebas/.gemini/antigravity/brain/a78072a2-83cd-4242-9935-27e1da602ecb/.system_generated/logs/transcript.jsonl", "r", encoding="utf-8") as f:
    lines = f.readlines()

import json
obj = json.loads(lines[980])
print("Step 980 tool_calls:")
for c in obj.get("tool_calls", []):
    print("Name:", c.get("name"))
    print("Args:", list(c.get("args", {}).keys()))
    if "Content" in c.get("args", {}):
        print(c.get("args", {})["Content"][:1500])
    if "CommandLine" in c.get("args", {}):
        print(c.get("args", {})["CommandLine"][:500])
