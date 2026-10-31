import os
import sys

sys.stdout.reconfigure(encoding='utf-8')

targets = [
    'carry forex g10',
    'drif',
    'cuartos',
    'xauusd / xagusd',
    'night',
    'rsi(2)',
    'msnr',
]

for root, dirs, files in os.walk('dashboard'):
    for f in files:
        if f.endswith('.py'):
            fp = os.path.join(root, f)
            with open(fp, 'r', encoding='utf-8', errors='ignore') as file:
                for idx, line in enumerate(file):
                    l_lower = line.lower()
                    for t in targets:
                        if t in l_lower:
                            # print filename, line number, and text
                            print(f'{fp}:{idx+1} [{t}]: {line.strip()[:100]}')
                            break
