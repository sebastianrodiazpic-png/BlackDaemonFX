import json
import re

with open('dashboard/strategy_bases_page.py', 'r', encoding='utf-8') as f:
    content = f.read()

m = re.search(r'const WINNERS_DATA = (\[.*?\]);', content, re.DOTALL)
if m:
    data = json.loads(m.group(1))
    multi = [d for d in data if d.get('strategy') == 'MultiStrategia']
    print(f"Total WINNERS_DATA: {len(data)}, MultiStrategia: {len(multi)}")
    symbols_multi = {}
    for d in multi:
        symbols_multi[d['symbol']] = symbols_multi.get(d['symbol'], 0) + 1
    print(f"Unique symbols in MultiStrategia: {len(symbols_multi)}")
    print("Multi entries by category:")
    cats = {}
    for d in multi:
        cat = d.get('category', 'Unknown')
        cats[cat] = cats.get(cat, 0) + 1
    for k, v in cats.items():
        print(f"  {k}: {v}")
else:
    print("WINNERS_DATA not found")
