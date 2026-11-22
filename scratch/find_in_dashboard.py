with open('dashboard/realtime_dashboard.py', encoding='utf-8') as f:
    lines = f.readlines()
for i, l in enumerate(lines):
    if any(k in l for k in ['26082032', 'strategy_origin', '"ICT":', 'isMultiStrat']):
        print(f'{i+1}: {l.strip()[:110]}')
