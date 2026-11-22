import json, re

with open('dashboard/strategy_bases_page.py', 'r', encoding='utf-8') as f:
    content = f.read()

m = re.search(r'const WINNERS_DATA = (\[.*?\]);', content, re.DOTALL)
if m:
    data = json.loads(m.group(1))
    single = [d for d in data if d.get('strategy') != 'MultiStrategia']
    multi = [d for d in data if d.get('strategy') == 'MultiStrategia']
    print(f"Total: {len(data)}, Single: {len(single)}, Multi: {len(multi)}")
    
    # Check if single strategies match the 5y comparative table or 2y
    print("\nSample single strategy items:")
    for d in single[:5]:
        print(f"  {d['symbol']} ({d['strategy']}): trades={d['trades']}, wr={d['win_rate']}, pnl={d['pnl']}")
