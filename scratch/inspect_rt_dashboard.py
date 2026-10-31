import sys

sys.stdout.reconfigure(encoding='utf-8')

targets = [
    'carry',
    'drif',
    'cuartos',
    'xauusd / xagusd',
    'night',
    'rsi(2)',
    'msnr',
]

with open('dashboard/realtime_dashboard.py', 'r', encoding='utf-8', errors='ignore') as f:
    lines = f.readlines()

for idx, line in enumerate(lines):
    l_lower = line.lower()
    for t in targets:
        if t in l_lower:
            print(f'Line {idx+1}: {line.rstrip()[:120]}')
            break
