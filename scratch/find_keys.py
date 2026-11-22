with open('dashboard/realtime_dashboard.py', 'r', encoding='utf-8') as f:
    for idx, line in enumerate(f):
        if '"ICT":' in line or '"INDICESB_SNR":' in line:
            print(f'Line {idx+1}: {line.strip()[:60]}')
