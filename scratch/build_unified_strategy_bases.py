import re
import json
import sys

sys.stdout.reconfigure(encoding='utf-8')

# Read current file to get WINNERS_DATA, LOSERS_DATA, and panel HTMLs
with open('dashboard/strategy_bases_page.py', 'r', encoding='utf-8') as f:
    orig_text = f.read()

m_winners = re.search(r'const WINNERS_DATA = (\[.*?\]);', orig_text, re.DOTALL)
if not m_winners:
    raise ValueError("WINNERS_DATA not found")
winners_json_str = m_winners.group(1)

m_losers = re.search(r'const LOSERS_DATA = (\[.*?\]);', orig_text, re.DOTALL)
if not m_losers:
    raise ValueError("LOSERS_DATA not found")
losers_json_str = m_losers.group(1)

winners_data = json.loads(winners_json_str)
losers_data = json.loads(losers_json_str)

print(f"Loaded {len(winners_data)} winners items, {len(losers_data)} losers items.")
print(f"Profitable items: {len([w for w in winners_data if w.get('is_profitable')])}")
