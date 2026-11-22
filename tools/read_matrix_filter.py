import sys
sys.stdout.reconfigure(encoding='utf-8')
with open('dashboard/realtime_dashboard.py', 'r', encoding='utf-8') as f:
    text = f.read()

idx = text.find('let currentMatrixFilter')
if idx == -1:
    idx = text.find('currentMatrixFilter')
print(text[idx-50:idx+800])
