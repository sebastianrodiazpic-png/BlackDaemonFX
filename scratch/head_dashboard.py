with open('dashboard/realtime_dashboard.py', 'r', encoding='utf-8', errors='ignore') as f:
    lines = f.readlines()

for i in range(min(80, len(lines))):
    print(f'{i+1}: {lines[i].strip()[:100]}')
