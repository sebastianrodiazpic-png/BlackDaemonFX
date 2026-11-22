# -*- coding: utf-8 -*-
import re
import sys

sys.stdout.reconfigure(encoding='utf-8')

with open('dashboard/strategy_bases_page.py', 'r', encoding='utf-8') as f:
    html = f.read()

body_idx = html.find('<body>')
script_idx = html.find('<script>')
body_content = html[body_idx:script_idx]

pos = 0
depth = 0
for m in re.finditer(r'(<div\b[^>]*>|</div\s*>)', body_content, re.IGNORECASE):
    t = m.group(1)
    if t.startswith('</'):
        depth -= 1
    else:
        depth += 1
    # Check at interesting landmarks
    sub = body_content[m.start():m.start()+80].replace('\n', ' ')
    if any(k in sub for k in ['id="triMotorAuditPanel"', 'id="msnrAuditPanel"', 'id="orbAuditPanel"', 'id="ictAuditPanel"', 'id="trendPullbackAuditPanel"', '<section class="kpi', 'id="tpAnalytics"', 'id="tabPanelAll"', '<table id="winnersTable"', 'id="portfolioStagingSection"']):
        print(f"Landmark depth={depth}: {sub[:60]}")

print("Final depth:", depth)
