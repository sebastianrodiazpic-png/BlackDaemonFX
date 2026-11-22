import re
import sys

sys.stdout.reconfigure(encoding='utf-8')

with open('dashboard/strategy_bases_page.py', 'r', encoding='utf-8') as f:
    text = f.read()

idx = text.find('id="statusFilterAll"')
print(text[idx-200:idx+800])
