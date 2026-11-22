import re
import sys

sys.stdout.reconfigure(encoding='utf-8')

with open('dashboard/strategy_bases_page.py', 'r', encoding='utf-8') as f:
    text = f.read()

idx = text.find('Fundamentos y Reglas de Ejecución')
print("Position:", idx)
start = max(0, idx - 400)
end = min(len(text), idx + 2000)
print(text[start:end])
