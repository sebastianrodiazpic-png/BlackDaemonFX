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
render_idx = content.find('function render(', script_start)
render_end = content.find('function toggle(', render_idx)
print("=== RENDER FUNCTION ===")
print(content[render_idx:render_end])
