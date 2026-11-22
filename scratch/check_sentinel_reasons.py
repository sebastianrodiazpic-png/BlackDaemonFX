with open('strategy/regime/market_regime_sentinel.py', 'r', encoding='utf-8', errors='ignore') as f:
    lines = f.readlines()

for idx, l in enumerate(lines):
    if 'reason' in l and ('=' in l or 'return' in l or 'f"' in l or "f'" in l):
        print(f"{idx+1}: {l.strip()[:100]}")
