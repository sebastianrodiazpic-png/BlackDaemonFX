import json

log_path = 'C:/Users/sebas/.gemini/antigravity/brain/628b30b0-7a0a-478f-b382-dc75381f7c0a/.system_generated/logs/transcript.jsonl'
with open(log_path, 'r', encoding='utf-8') as f:
    for line in f:
        try:
            d = json.loads(line)
            c = str(d.get('content', ''))
            t = str(d.get('thinking', ''))
            for text, name in [(c, 'content'), (t, 'thinking')]:
                if 'CENSO COMPLETO' in text or 'Jump 75 Index' in text or '602.8' in text:
                    print(f"Step {d.get('step_index')} in {name} ({d.get('source')}): {text[:250]}...\n")
        except:
            pass
