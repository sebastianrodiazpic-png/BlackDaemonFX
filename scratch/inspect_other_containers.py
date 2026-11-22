import re
import sys

sys.stdout.reconfigure(encoding='utf-8')

with open('dashboard/strategy_bases_page.py', 'r', encoding='utf-8') as f:
    text = f.read()

for cls in [r'\.tab-bar[^{]*\{', r'\.kpi-grid[^{]*\{', r'\.tp-chart-container[^{]*\{']:
    m = re.search(cls + r'[^}]+}', text)
    if m:
        print(f"=== {cls} ===")
        print(m.group(0))
