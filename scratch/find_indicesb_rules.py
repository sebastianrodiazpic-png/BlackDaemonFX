with open('strategy/execution/worker_rules.py', encoding='utf-8') as f:
    lines = f.readlines()

for i, l in enumerate(lines):
    if any(k in l for k in ['INDICES', 'indices']):
        print(f'{i+1}: {l.strip()[:100]}')
