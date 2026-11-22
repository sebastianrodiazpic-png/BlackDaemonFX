# -*- coding: utf-8 -*-
with open("C:/Users/sebas/.gemini/antigravity/brain/a78072a2-83cd-4242-9935-27e1da602ecb/.system_generated/logs/transcript.jsonl", "r", encoding="utf-8") as f:
    text = f.read()

import re
matches = [m.start() for m in re.finditer(r'daemon_card_css = \'\'\'', text)]
if matches:
    idx = matches[0]
    print(text[idx:idx+4500])
