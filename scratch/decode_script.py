# -*- coding: utf-8 -*-
with open("scratch/step_363_code.py", "r", encoding="utf-8") as f:
    text = f.read()

# text is a string literal starting with "
if text.startswith('"') and text.endswith('"'):
    # unescape
    text = text[1:-1].encode('utf-8').decode('unicode_escape')

with open("scratch/decoded_step_363.py", "w", encoding="utf-8") as out:
    out.write(text)

print("Decoded length:", len(text))
