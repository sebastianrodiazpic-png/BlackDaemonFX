import json
import re
import sys

sys.stdout.reconfigure(encoding='utf-8')

with open('dashboard/strategy_bases_page.py', 'r', encoding='utf-8') as f:
    text = f.read()

m = re.search(r'const WINNERS_DATA = (\[.*?\]);', text, re.DOTALL)
data = json.loads(m.group(1))

from collections import Counter
status_counts = Counter(x.get('status') for x in data)
for s, c in status_counts.most_common():
    print(f"{c:3d}: {s}")
