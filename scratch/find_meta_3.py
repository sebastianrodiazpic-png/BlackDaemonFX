with open('dashboard/realtime_dashboard.py', encoding='utf-8') as f:
    text = f.read()

idx = text.find('_WORKER_PROFILE_META')
print(text[idx+3400:idx+5500])
