import os

for root, dirs, files in os.walk('.'):
    if '.venv' in root or '.git' in root or 'scratch' in root:
        continue
    for file in files:
        if file.endswith('.py'):
            p = os.path.join(root, file)
            try:
                with open(p, 'r', encoding='utf-8') as f:
                    txt = f.read()
                    if 'PRUNED_ASSET_UNIVERSE["ICT"]' in txt or "PRUNED_ASSET_UNIVERSE['ICT']" in txt or 'PRUNED_ASSET_UNIVERSE.get("ICT"' in txt:
                        print(f"Found in {p}")
            except Exception:
                pass
