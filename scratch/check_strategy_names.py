import glob, re

for fname in [
    'strategy/malaysian_snr/malaysian_snr_strategy.py',
    'strategy/ict/ict_strategy.py',
    'strategy/orb/new_york_orb.py',
]:
    with open(fname, 'r', encoding='utf-8', errors='ignore') as f:
        text = f.read()
    matches = re.findall(r'[\'"]strategy_name[\'"]\s*:\s*[\'"][^\'"]+[\'"]', text)
    print(fname, '->', set(matches))
