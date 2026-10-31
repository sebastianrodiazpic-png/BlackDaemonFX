import sys

sys.stdout.reconfigure(encoding='utf-8')

for fn in ['dashboard/performance_page.py', 'dashboard/strategy_bases_page.py']:
    with open(fn, 'r', encoding='utf-8', errors='ignore') as f:
        lines = f.readlines()
    for i, l in enumerate(lines):
        for term in ['carry', 'drif', 'cuartos', 'night', 'rsi(2)', 'rsi2']:
            if term in l.lower():
                print(f'{fn}:{i+1} [{term}]: {l.strip()[:100]}')
                break
