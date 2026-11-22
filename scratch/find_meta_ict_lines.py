with open('dashboard/realtime_dashboard.py', encoding='utf-8') as f:
    lines = f.readlines()

for i, l in enumerate(lines):
    if '"ICT": {' in l:
        print(f'Match at line {i+1}:')
        for j in range(i, min(i+25, len(lines))):
            print(f'{j+1}: {lines[j].rstrip()}')
