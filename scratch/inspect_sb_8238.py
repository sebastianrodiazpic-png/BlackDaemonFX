import sys

sys.stdout.reconfigure(encoding='utf-8')

with open('dashboard/strategy_bases_page.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

for i in range(8230, 8250):
    if i < len(lines):
        print(f"L{i+1}: {lines[i]}", end='')
