import sys, json, re
sys.path.insert(0, '.')
from dashboard.strategy_bases_page import STRATEGY_BASES_HTML

m_winners = re.search(r"const WINNERS_DATA = (\[.*?\]);", STRATEGY_BASES_HTML, re.S)
winners = json.loads(m_winners.group(1))

from collections import Counter
counts = Counter(w["strategy"] for w in winners)
print("Winners counts by strategy:", counts)
