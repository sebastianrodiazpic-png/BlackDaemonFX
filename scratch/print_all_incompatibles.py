import re
import sys

sys.stdout.reconfigure(encoding='utf-8')

with open('dashboard/strategy_bases_page.py', 'r', encoding='utf-8') as f:
    text = f.read()

lines = text.splitlines()
for idx, line in enumerate(lines):
    if re.search(r'incompatib', line, re.IGNORECASE):
        print(f"L{idx+1}: {line.strip()[:140]}")
