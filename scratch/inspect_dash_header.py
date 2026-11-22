import re
import sys

sys.stdout.reconfigure(encoding='utf-8')

with open('dashboard/realtime_dashboard.py', 'r', encoding='utf-8') as f:
    text = f.read()

m = re.search(r'<div class="top">.*?</div>\s*</div>', text, re.DOTALL)
if m:
    print("Found header in realtime_dashboard.py:")
    print(m.group(0))
else:
    print("Header not found in realtime_dashboard.py")
