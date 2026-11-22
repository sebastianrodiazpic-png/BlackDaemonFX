import sys

sys.stdout.reconfigure(encoding='utf-8')

with open('dashboard/realtime_dashboard.py', 'r', encoding='utf-8') as f:
    text = f.read()

start_marker = "_INSTRUMENTS_HTML = r'''"
end_marker = "\n'''\n\n\n\n_HTML = with_page_loading(_HTML)"
s_idx = text.find(start_marker)
e_idx = text.find(end_marker, s_idx)
content = text[s_idx + len(start_marker):e_idx]

script_start = content.find('<script>')
script_text = content[script_start:]

import re
matches = list(re.finditer(r'function render[A-Za-z0-9_]*\(', script_text))
for m in matches:
    print(m.group(0))

render_idx = script_text.find('function render(')
if render_idx == -1:
    render_idx = script_text.find('function render')
print("\n=== render function excerpt ===")
print(script_text[render_idx:render_idx+3500])
