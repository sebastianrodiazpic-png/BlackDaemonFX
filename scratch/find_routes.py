with open('dashboard/realtime_dashboard.py', 'r', encoding='utf-8', errors='ignore') as f:
    lines = f.readlines()

for i, l in enumerate(lines):
    if any(k in l for k in ['def get(', 'def post(', 'add_get(', 'add_post(', 'add_routes', '@app.']):
        print(f'{i+1}: {l.strip()[:100]}')
