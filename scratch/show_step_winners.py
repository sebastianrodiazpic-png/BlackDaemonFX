import json, re

with open('dashboard/strategy_bases_page.py', 'r', encoding='utf-8', errors='ignore') as f:
    text = f.read()

m = re.search(r'const\s+WINNERS_DATA\s*=\s*(\[.*?\]);', text, re.DOTALL)
if m:
    data = json.loads(m.group(1))
    step_items = [d for d in data if 'step' in d.get('symbol', '').lower()]
    for item in step_items:
        print(f"{item['strategy']} | {item['symbol']} | Trades: {item['trades']} | WR: {item['win_rate']}% | PnL: ${item['pnl']} | Rank: {item.get('rank')}")
