# -*- coding: utf-8 -*-
with open("C:/Users/sebas/.gemini/antigravity/brain/a78072a2-83cd-4242-9935-27e1da602ecb/.system_generated/logs/transcript.jsonl", "r", encoding="utf-8") as f:
    lines = f.readlines()

import json
obj = json.loads(lines[363])
c = obj.get("tool_calls", [])[0]
print(c.get("args", {})["Content"])
