import re
import sys

sys.stdout.reconfigure(encoding='utf-8')

with open('dashboard/strategy_bases_page.py', 'r', encoding='utf-8') as f:
    text = f.read()

m = re.search(r'<div class="status-filters">.*?</div>\s*</div>', text, re.DOTALL)
if m:
    print(m.group(0))
else:
    # search where statusFilter is
    idx = text.find('statusFilter')
    if idx != -1:
        print(text[idx-100:idx+400])
