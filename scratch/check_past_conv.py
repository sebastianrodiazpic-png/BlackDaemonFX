import json

path = r"C:\Users\sebas\.gemini\antigravity\brain\4d48489e-f8b3-48bc-9d0e-e5a862673f42\.system_generated\logs\transcript.jsonl"
with open(path, "r", encoding="utf-8") as f:
    for line in f:
        obj = json.loads(line)
        if obj.get("type") == "USER_INPUT":
            print("USER_INPUT:", obj.get("content", "")[:300])
            print("="*60)
        elif obj.get("type") == "PLANNER_RESPONSE":
            for tc in obj.get("tool_calls", []):
                name = tc.get("name") or tc.get("function", {}).get("name")
                args = tc.get("arguments") or tc.get("args") or tc.get("function", {}).get("arguments")
                if isinstance(args, str):
                    try:
                        args = json.loads(args)
                    except:
                        pass
                if name in ("replace_file_content", "write_to_file"):
                    tf = args.get("TargetFile") if isinstance(args, dict) else args
                    print(f"EDIT: {name} -> {tf}")
