import sys

sys.stdout.reconfigure(encoding='utf-8')

with open('dashboard/realtime_dashboard.py', 'r', encoding='utf-8', errors='ignore') as f:
    lines = f.readlines()

phrases = [
    'Carry Forex G10',
    'DRIF',
    'Cuartos',
    'RSI(2)',
    'NIGHT',
    'MSNR',
]

for i, l in enumerate(lines):
    for p in phrases:
        if p in l:
            print(f'{i+1} [{p}]: {l.strip()[:110]}')
            break
