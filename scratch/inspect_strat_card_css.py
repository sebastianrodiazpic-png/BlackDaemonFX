import re
import sys

sys.stdout.reconfigure(encoding='utf-8')

with open('dashboard/strategy_bases_page.py', 'r', encoding='utf-8') as f:
    text = f.read()

for cls in [r'\.strategy-grid\s*\{', r'\.strat-card\s*\{', r'\.strat-rule\s*\{', r'\.strat-stats\s*\{']:
    m = re.search(cls + r'[^}]+}', text)
    if m:
        print(m.group(0))
