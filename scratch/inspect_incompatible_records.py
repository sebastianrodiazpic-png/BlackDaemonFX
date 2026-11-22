import json
import re
import sys

sys.stdout.reconfigure(encoding='utf-8')

with open('dashboard/strategy_bases_page.py', 'r', encoding='utf-8') as f:
    text = f.read()

m = re.search(r'const WINNERS_DATA = (\[.*?\]);', text, re.DOTALL)
if m:
    data = json.loads(m.group(1))
    print(f"Total records in WINNERS_DATA: {len(data)}")
    incompatibles = [x for x in data if 'incompatible' in x.get('status', '').lower()]
    print(f"Incompatible records in WINNERS_DATA: {len(incompatibles)}")
    for x in incompatibles[:10]:
        print(f"  {x.get('symbol')} | {x.get('strategy')} | {x.get('status')} | trades={x.get('trades')}")

m2 = re.search(r'const LOSERS_DATA = (\[.*?\]);', text, re.DOTALL)
if m2:
    data2 = json.loads(m2.group(1))
    print(f"Total records in LOSERS_DATA: {len(data2)}")
    incompatibles2 = [x for x in data2 if 'incompatible' in x.get('status', '').lower()]
    print(f"Incompatible records in LOSERS_DATA: {len(incompatibles2)}")
