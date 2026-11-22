with open('dashboard/realtime_dashboard.py', 'r', encoding='utf-8') as f:
    text = f.read()

idx = text.find('.matrixTabBtn')
if idx != -1:
    print(text[idx:idx+800])
else:
    print('matrixTabBtn not found in CSS')
