import re

with open('strategy/ict/ict_strategy.py', 'r', encoding='utf-8') as f:
    text = f.read()

matches = re.findall(r'"reason":\s*([^,\}\n]+)', text)
print(f"Total reasons: {len(matches)}")
for m in sorted(set(matches)):
    print(" ", m.strip())
