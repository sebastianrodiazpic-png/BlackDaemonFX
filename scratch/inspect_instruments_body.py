import sys

sys.stdout.reconfigure(encoding='utf-8')

with open('dashboard/realtime_dashboard.py', 'r', encoding='utf-8') as f:
    text = f.read()

start_marker = "_INSTRUMENTS_HTML = r'''"
end_marker = "\n'''\n\n\n\n_HTML = with_page_loading(_HTML)"
s_idx = text.find(start_marker)
e_idx = text.find(end_marker, s_idx)
content = text[s_idx + len(start_marker):e_idx]

import re
body_start = content.find('<body>')
script_start = content.find('<script>')
print("=== HTML BODY CONTENT (first 3000 chars) ===")
print(content[body_start:body_start+3000])

print("\n=== SCRIPT CONTENT (first 2500 chars) ===")
print(content[script_start:script_start+2500])
