import sys
sys.stdout.reconfigure(encoding='utf-8')

with open('dashboard/strategy_bases_page.py', 'r', encoding='utf-8') as f:
    html = f.read()

body_idx = html.find('<div class="top">')
idx_tri = html.find('id="triMotorAuditPanel"')
print(html[body_idx:idx_tri])
