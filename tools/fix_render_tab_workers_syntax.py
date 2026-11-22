# -*- coding: utf-8 -*-
"""
Corrige la función renderTabWorkers en dashboard/realtime_dashboard.py
eliminando la doble declaración de 'const panel' y asegurando que la sintaxis
sea 100% válida en Node.js y en los navegadores.
"""
import subprocess
import re

with open('dashboard/realtime_dashboard.py', 'r', encoding='utf-8') as f:
    text = f.read()

idx = text.find('function renderTabWorkers')
idx_next = text.find('function renderNews', idx)

old_function = text[idx:idx_next]

new_function = '''function renderTabWorkers(s) {
        const banner = $('strategyHighlightBanner');
        if (banner) {
          banner.style.display = 'none';
          banner.innerHTML = '';
        }
        const panel = $('tabWorkerPanel');
        if (panel) {
          panel.style.display = 'none';
          panel.innerHTML = '';
        }
      }

      '''

text = text[:idx] + new_function + text[idx_next:]

with open('dashboard/realtime_dashboard.py', 'w', encoding='utf-8') as f:
    f.write(text)

print("renderTabWorkers reemplazada cleanly.")

# Ahora verificar la sintaxis de todos los <script> en _INSTRUMENTS_HTML
from dashboard.realtime_dashboard import _INSTRUMENTS_HTML

scripts = re.findall(r'<script>(.*?)</script>', _INSTRUMENTS_HTML, re.DOTALL)
print('Total script tags in _INSTRUMENTS_HTML:', len(scripts))
for i, s in enumerate(scripts):
    with open(f'storage/test_instruments_script_{i}.js', 'w', encoding='utf-8') as f:
        f.write(s)
    res = subprocess.run(['node', '--check', f'storage/test_instruments_script_{i}.js'], capture_output=True, text=True)
    print(f'Script {i} return code: {res.returncode}')
    if res.returncode != 0:
        print(f'Script {i} stderr: {res.stderr}')
    assert res.returncode == 0, f"Script {i} failed syntax check!"

print("¡Todos los scripts de _INSTRUMENTS_HTML pasaron la verificación de sintaxis de Node.js exitosamente!")
