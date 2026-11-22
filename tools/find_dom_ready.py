import re

with open('dashboard/strategy_bases_page.py', 'r', encoding='utf-8') as f:
    text = f.read()

matches = [m.start() for m in re.finditer(r'renderWinnersTable|DOMContentLoaded|window\.onload', text)]
print(f"Found {len(matches)} occurrences")
for pos in matches[:5]:
    print(text[pos:pos+200])
    print('---')
