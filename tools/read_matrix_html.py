with open('dashboard/realtime_dashboard.py', 'r', encoding='utf-8') as f:
    text = f.read()

idx = text.find('id="confluenceMatrixCard"')
print(text[idx-50:idx+1500])
