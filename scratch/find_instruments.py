with open('dashboard/realtime_dashboard.py', 'r', encoding='utf-8', errors='ignore') as f:
    lines = f.readlines()

for i, l in enumerate(lines):
    if any(k in l for k in ['def _build_instruments', 'INSTRUMENTS_HTML', 'renderInstruments', 'category_labels', 'catalog.append', 'DEFAULT_PRIORITIZED_SYMBOLS']):
        print(f'{i+1}: {l.strip()[:100]}')
