import re
import sys

sys.stdout.reconfigure(encoding='utf-8')

with open('dashboard/strategy_bases_page.py', 'r', encoding='utf-8') as f:
    html = f.read()

# Pattern to remove the old nav block right after the top header
old_nav_pattern = re.compile(
    r'</div>\s*<div class="nav">.*?</div>\s*</div>\s*(?=<!-- BARRA DE PESTAÑAS)',
    re.DOTALL
)

m = old_nav_pattern.search(html)
if m:
    print("Found old nav block:", repr(m.group(0)[:100]))
    # Replace with just </div> which closes .top
    html = html[:m.start()] + '</div>\n\n      ' + html[m.end():]
    with open('dashboard/strategy_bases_page.py', 'w', encoding='utf-8') as f:
        f.write(html)
    print("Removed duplicate nav block.")
else:
    print("Old nav block not found.")
