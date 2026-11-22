import re
import sys

sys.stdout.reconfigure(encoding='utf-8')

with open('dashboard/strategy_bases_page.py', 'r', encoding='utf-8') as f:
    text = f.read()

m = re.search(r'<table id="losersTable">.*?</table>', text, re.DOTALL)
if m:
    print("=== losersTable HTML ===")
    print(m.group(0))

m2 = re.search(r'function renderLosersTable\(\).*?tbody\.appendChild\(tr\);\s*\}\);', text, re.DOTALL)
if m2:
    print("=== renderLosersTable JS ===")
    print(m2.group(0)[-1500:])
