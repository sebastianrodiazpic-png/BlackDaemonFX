import json, re

with open('dashboard/strategy_bases_page.py', 'r', encoding='utf-8') as f:
    content = f.read()

m = re.search(r'const WINNERS_DATA = (\[.*?\]);', content, re.DOTALL)
if m:
    data = json.loads(m.group(1))
    strategies = {}
    for d in data:
        s = d.get('strategy')
        strategies[s] = strategies.get(s, 0) + 1
    print("Strategies in WINNERS_DATA:")
    for k, v in strategies.items():
        print(f"  {k}: {v}")
