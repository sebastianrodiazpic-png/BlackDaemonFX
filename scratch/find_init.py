with open('dashboard/realtime_dashboard.py', 'r', encoding='utf-8') as f:
    text = f.read()

idx = text.find('class RealtimeDashboardService')
init_idx = text.find('def __init__', idx)
print(text[init_idx:init_idx+2000])
