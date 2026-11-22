import re

files = [
    ('dashboard/realtime_dashboard.py (Dashboard)', 'dashboard/realtime_dashboard.py', '_HTML ='),
    ('dashboard/realtime_dashboard.py (Instruments)', 'dashboard/realtime_dashboard.py', '_INSTRUMENTS_HTML ='),
    ('dashboard/account_page.py', 'dashboard/account_page.py', None),
    ('dashboard/performance_page.py', 'dashboard/performance_page.py', None),
    ('dashboard/strategy_bases_page.py', 'dashboard/strategy_bases_page.py', None),
]

for label, path, marker in files:
    with open(path, 'r', encoding='utf-8') as f:
        text = f.read()
    start_search = 0
    if marker:
        start_search = text.find(marker)
    aside_start = text.find('<aside class="brandSidebar">', start_search)
    aside_end = text.find('</aside>', aside_start) + len('</aside>')
    print(f"=== {label} ===")
    print(text[aside_start:aside_end])
    print()
