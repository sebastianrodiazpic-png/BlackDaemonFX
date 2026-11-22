import re

with open('dashboard/strategy_bases_page.py', 'r', encoding='utf-8') as f:
    text = f.read()

matches = list(re.finditer(r'Sabri\s*Malle', text, re.IGNORECASE))
print(f"Total matches in strategy_bases_page.py: {len(matches)}")
for i, m in enumerate(matches[:15]):
    print(f"[{i+1}] {text[max(0, m.start()-40):min(len(text), m.end()+40)]}")
