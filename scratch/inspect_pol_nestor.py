with open("scratch/transcripts/sTRxqo4EwPU.txt", "r", encoding="utf-8") as f:
    text_pol = f.read()

with open("scratch/transcripts/1x57n_5iRsU.txt", "r", encoding="utf-8") as f:
    text_nestor = f.read()

print("POL CASTELLA SNIPPETS:")
for i, line in enumerate(text_pol.split('.')):
    if any(k in line.lower() for k in ["soporte", "resistencia", "vela", "línea", "estrategia"]):
        print(f" - {line.strip()}")
    if i > 25:
        break

print("\nNESTOR SANTOS SNIPPETS:")
for i, line in enumerate(text_nestor.split('.')):
    if any(k in line.lower() for k in ["soporte", "resistencia", "vela", "cierre", "mecha"]):
        print(f" - {line.strip()}")
    if i > 25:
        break
