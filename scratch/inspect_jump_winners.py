import json

with open('dashboard/strategy_bases_page.py', 'r', encoding='utf-8') as f:
    text = f.read()

start_marker = 'const WINNERS_DATA = '
start_idx = text.find(start_marker)
end_idx = text.find('];\n', start_idx)
if end_idx == -1:
    end_idx = text.find('];', start_idx)

data = json.loads(text[start_idx + len(start_marker):end_idx + 1])
multi_items = [d for d in data if d.get('strategy') == 'MultiStrategia']

print(f"Total MultiStrategia rows in WINNERS_DATA: {len(multi_items)}")
cats = set(d.get('category') for d in multi_items)
for c in sorted(cats):
    items = [d for d in multi_items if d.get('category') == c]
    print(f"\nCategory: {c} ({len(items)} items)")
    for it in items[:4]:
        print(f"  - {it.get('symbol')}: trades={it.get('trades')}, wr={it.get('win_rate')}%, pnl={it.get('pnl')}")
