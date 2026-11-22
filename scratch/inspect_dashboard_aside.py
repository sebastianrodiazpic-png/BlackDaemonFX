with open('dashboard/realtime_dashboard.py', 'r', encoding='utf-8') as f:
    text = f.read()

pos = text.find('_HTML =')
body_pos = text.find('<aside class="brandSidebar">', pos)
print(f"aside pos: {body_pos}")
print(text[body_pos:body_pos+1500])
