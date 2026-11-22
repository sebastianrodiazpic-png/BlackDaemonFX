# -*- coding: utf-8 -*-
with open("C:/Users/sebas/.gemini/antigravity/brain/a78072a2-83cd-4242-9935-27e1da602ecb/.system_generated/logs/transcript.jsonl", "r", encoding="utf-8") as f:
    lines = f.readlines()

import json, ast
obj = json.loads(lines[363])
content_str = obj.get("tool_calls", [])[0]["args"]["Content"]
try:
    code = ast.literal_eval(content_str)
except Exception:
    code = content_str

with open("scratch/step_363_code.py", "w", encoding="utf-8") as out:
    out.write(code)

print("Saved step_363_code.py successfully!")
