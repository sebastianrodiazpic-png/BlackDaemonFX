import json, re
with open("dashboard/strategy_bases_page.py", "r", encoding="utf-8") as f:
    text = f.read()

# Buscar bloques JSON de activos
matches = re.findall(r'\{\s*"rank":\s*\d+,\s*"symbol":\s*"([^"]+)",\s*"strategy":\s*"([^"]+)"[^\}]+\}', text)
print(f"Total rank matches: {len(matches)}")
msnr_matches = [m for m in matches if "Malaysian" in m[1]]
print(f"Total MSNR rank matches: {len(msnr_matches)}")
for m in msnr_matches[:10]:
    print(m)

# Buscar en podados
pruned = re.findall(r'\{\s*"symbol":\s*"([^"]+)",\s*"strategy":\s*"([^"]+)"[^\}]+\}', text)
msnr_pruned = [p for p in pruned if "Malaysian" in p[1]]
print(f"Total MSNR pruned: {len(msnr_pruned)}")
for p in msnr_pruned:
    print(p)
