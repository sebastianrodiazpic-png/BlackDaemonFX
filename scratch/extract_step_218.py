import json

with open('C:/Users/sebas/.gemini/antigravity/brain/628b30b0-7a0a-478f-b382-dc75381f7c0a/.system_generated/logs/transcript_full.jsonl', 'r', encoding='utf-8') as f:
    for line in f:
        try:
            d = json.loads(line)
            if d.get('step_index') == 218:
                content = d.get('content', '')
                with open('scratch/step_218_censo.md', 'w', encoding='utf-8') as out:
                    out.write(content)
                print(f"Wrote {len(content)} chars to scratch/step_218_censo.md")
                break
        except Exception as e:
            pass
