import sys
sys.path.insert(0, '.')
from dashboard.strategy_bases_page import STRATEGY_BASES_HTML
import re
print('msnrAuditPanel in html:', 'id="msnrAuditPanel"' in STRATEGY_BASES_HTML)
matches = list(re.finditer(r'.{0,40}Malaysian SNR.{0,40}', STRATEGY_BASES_HTML))
print(f"Total Malaysian SNR matches: {len(matches)}")
for m in matches[:5]:
    print(" ", m.group(0).strip())
