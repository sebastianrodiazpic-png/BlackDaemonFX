import os
import sys

sys.stdout.reconfigure(encoding='utf-8')

targets = [
    'Carry Forex G10',
    'DRIF',
    'Cuartos',
    'XAUUSD / XAGUSD',
    'NIGHT',
    'RSI(2) diario',
    'MSNR',
]

for root, dirs, files in os.walk('.'):
    if any(p in root for p in ['.git', '.venv', '__pycache__', 'graphify-out', 'storage', 'data', 'artifacts']):
        continue
    for file in files:
        if file.endswith(('.py', '.html', '.js')):
            fp = os.path.join(root, file)
            with open(fp, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            matches = [t for t in targets if t in content]
            if matches and ('dashboard' in fp or 'main' in fp or 'reporting' in fp or 'service' in fp):
                print(f'{fp}: {matches}')
