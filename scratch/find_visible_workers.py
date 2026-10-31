with open('dashboard/realtime_dashboard.py', 'r', encoding='utf-8', errors='ignore') as f:
    lines = f.readlines()

for i, l in enumerate(lines):
    if 'visibleWorkers' in l or 'function visibleWorkers' in l:
        print(f'{i+1}: {l.strip()[:100]}')
