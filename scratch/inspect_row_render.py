import re
import sys

sys.stdout.reconfigure(encoding='utf-8')

with open('dashboard/strategy_bases_page.py', 'r', encoding='utf-8') as f:
    text = f.read()

m = re.search(r'function renderWinnersTable\(\).*?tbody\.appendChild\(tr\);\s*\}\);', text, re.DOTALL)
if m:
    print(m.group(0)[-2000:])
