import json
import os

p = r"C:\Users\sebas\.gemini\antigravity\brain\4d48489e-f8b3-48bc-9d0e-e5a862673f42\.system_generated\logs\transcript.jsonl"
with open(p, "r", encoding="utf-8", errors="ignore") as f:
    for line in f:
        if '"step_index":574' in line:
            obj = json.loads(line)
            print("STEP 574 CONTENT:")
            print(obj.get("content"))
            break
