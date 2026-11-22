import re
import sys

sys.stdout.reconfigure(encoding='utf-8')

with open('dashboard/strategy_bases_page.py', 'r', encoding='utf-8') as f:
    text = f.read()

for cls in [r'\.wrap\b[^{]*\{', r'\.w\b[^{]*\{', r'\.table-wrapper[^{]*\{', r'#winnersTable[^{]*\{']:
    m = re.search(cls + r'[^}]+}', text)
    if m:
        print(f"=== {cls} ===")
        print(m.group(0))
