with open('dashboard/realtime_dashboard.py', 'r', encoding='utf-8') as f:
    text = f.read()

pos = text.find('_HTML =')
print(f"_HTML pos: {pos}")
nav_pos = text.find('brandSidebar', pos)
print(f"brandSidebar pos: {nav_pos}")
print(text[nav_pos:nav_pos+2000])
