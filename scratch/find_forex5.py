with open('dashboard/realtime_dashboard.py', encoding='utf-8') as f:
    lines = f.readlines()

for i, l in enumerate(lines):
    if '26082205' in l or 'FOREX_5' in l:
        print(f'{i+1}: {l.strip()[:110]}')
