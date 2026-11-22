import sys
sys.path.insert(0, '.')
sys.stdout.reconfigure(encoding='utf-8')
from dashboard.strategy_bases_page import STRATEGY_BASES_HTML

with open('storage/sample_strategy_bases.html', 'w', encoding='utf-8') as f:
    f.write(STRATEGY_BASES_HTML)

print("Saved storage/sample_strategy_bases.html successfully.")
