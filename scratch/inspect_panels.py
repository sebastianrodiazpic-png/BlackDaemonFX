# -*- coding: utf-8 -*-
with open("dashboard/strategy_bases_page.py", "r", encoding="utf-8") as f:
    text = f.read()

import re
print("msnrAuditPanel in text:", "msnrAuditPanel" in text)
m_msnr = re.search(r'<div id="msnrAuditPanel".*?</div>\s*</div>\s*</div>', text, re.DOTALL)
if m_msnr:
    print("msnr snippet:", m_msnr.group(0)[:300])

print("orbAuditPanel in text:", "orbAuditPanel" in text)
m_orb = re.search(r'<div id="orbAuditPanel".*?</div>\s*</div>\s*</div>', text, re.DOTALL)
if m_orb:
    print("orb snippet:", m_orb.group(0)[:300])

print("ictAuditPanel in text:", "ictAuditPanel" in text)
m_ict = re.search(r'<div id="ictAuditPanel".*?</div>\s*</div>\s*</div>', text, re.DOTALL)
if m_ict:
    print("ict snippet:", m_ict.group(0)[:300])

print("trendPullbackAuditPanel in text:", "trendPullbackAuditPanel" in text)
m_tp = re.search(r'<div id="trendPullbackAuditPanel".*?</div>\s*</div>\s*</div>', text, re.DOTALL)
if m_tp:
    print("tp snippet:", m_tp.group(0)[:300])
