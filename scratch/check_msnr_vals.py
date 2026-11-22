import sys, json, re
sys.path.insert(0, '.')
from dashboard.strategy_bases_page import STRATEGY_BASES_HTML
m_winners = re.search(r"const WINNERS_DATA = (\[.*?\]);", STRATEGY_BASES_HTML, re.S)
winners = json.loads(m_winners.group(1))
for w in winners:
    if w["strategy"] == "Malaysian SNR" and w["symbol"] in ("XAUUSD", "BTCUSD", "ETHUSD", "AUDUSD"):
        print(w["symbol"], w["trades"], w["win_rate"], w["pnl"])
