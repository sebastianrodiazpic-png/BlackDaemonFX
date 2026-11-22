import re
import sys

sys.stdout.reconfigure(encoding='utf-8')

with open('dashboard/realtime_dashboard.py', 'r', encoding='utf-8') as f:
    text = f.read()

for cls in [r'\.top\s*\{', r'\.title\s*\{', r'\.sub\s*\{', r'\.actions\s*\{', r'\.badge\s*\{']:
    m = re.search(cls + r'[^}]+}', text)
    if m:
        print(m.group(0))
