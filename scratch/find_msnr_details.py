import json, re

with open("dashboard/strategy_bases_page.py", "r", encoding="utf-8") as f:
    text = f.read()

# Buscar bloques de USDCHF, AUDCAD, AUDUSD, Germany
for sym in ["USDCHF", "AUDCAD", "AUDUSD", "Germany 40", "GER40", "Germany"]:
    matches = re.findall(rf'\{{[^}}]*"symbol":\s*"{sym}"[^}}]*\}}', text)
    print(f"=== {sym} matches ({len(matches)}) ===")
    for m in matches:
        if "Malaysian" in m:
            print(m)
