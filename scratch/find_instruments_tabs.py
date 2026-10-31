with open('dashboard/realtime_dashboard.py', 'r', encoding='utf-8', errors='ignore') as f:
    lines = f.readlines()

in_html = False
for i, l in enumerate(lines[8560:9290]):
    line_num = 8561 + i
    if any(k in l for k in ['<nav', 'class="tab', 'data-tab', 'tabBtn', 'tab-btn', 'filterTab', 'nav-tab']):
        print(f'{line_num}: {l.strip()[:100]}')
