import re
import sys

sys.stdout.reconfigure(encoding='utf-8')

with open('dashboard/strategy_bases_page.py', 'r', encoding='utf-8') as f:
    text = f.read()

for cls in [r'\.table-wrapper\s*\{', r'table\s*\{', r'th\s*\{', r'td\s*\{', r'\.badge\s*\{']:
    m = re.search(cls + r'[^}]+}', text)
    if m:
        print(f"=== {cls} ===")
        print(m.group(0))
