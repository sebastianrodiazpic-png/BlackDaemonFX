import re
import sys

sys.stdout.reconfigure(encoding='utf-8')

for fname in ['dashboard/realtime_dashboard.py', 'dashboard/instruments_page.py', 'dashboard/strategy_bases_page.py']:
    with open(fname, 'r', encoding='utf-8') as f:
        text = f.read()
    m = re.search(r'<div class="top">.*?(?=<section|<div class="kpi|<div class="grid|<div class="filters)', text, re.DOTALL)
    if m:
        print(f"=== Header in {fname} ===")
        print(m.group(0).strip())
