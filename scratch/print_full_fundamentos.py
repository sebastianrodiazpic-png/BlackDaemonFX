import re
import sys

sys.stdout.reconfigure(encoding='utf-8')

with open('dashboard/strategy_bases_page.py', 'r', encoding='utf-8') as f:
    text = f.read()

m = re.search(r'(<section class="card"[^>]*>.*?Fundamentos y Reglas de Ejecuci[oó]n.*?</section>)', text, re.DOTALL)
if m:
    print(m.group(1))
