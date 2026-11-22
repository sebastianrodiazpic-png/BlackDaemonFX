with open('dashboard/realtime_dashboard.py', encoding='utf-8') as f:
    lines = f.readlines()

for i, l in enumerate(lines):
    if 'INDICESB_SNR' in l:
        print(f'{i+1}: {l.strip()[:100]}')
