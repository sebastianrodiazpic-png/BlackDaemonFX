import sys, json, re
sys.path.insert(0, '.')
from dashboard.strategy_bases_page import STRATEGY_BASES_HTML
m_winners = re.search(r"const WINNERS_DATA = (\[.*?\]);", STRATEGY_BASES_HTML, re.S)
winners = json.loads(m_winners.group(1))
msnr_symbols = [w["symbol"] for w in winners if w["strategy"] == "Malaysian SNR"]
print("MSNR symbols:", sorted(msnr_symbols)[:20])
print("EURUSD in MSNR?", "EURUSD" in msnr_symbols)
for w in winners:
    if "EURUSD" in w["symbol"]:
        print("EURUSD in:", w["strategy"], w["category"])
