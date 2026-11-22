import sys

sys.stdout.reconfigure(encoding='utf-8')

with open('dashboard/realtime_dashboard.py', 'r', encoding='utf-8') as f:
    text = f.read()

start_marker = "_INSTRUMENTS_HTML = r'''"
end_marker = "\n'''\n\n\n\n_HTML = with_page_loading(_HTML)"
if end_marker not in text:
    end_marker = "\n'''"

s_idx = text.find(start_marker)
e_idx = text.find(end_marker, s_idx)

if s_idx != -1 and e_idx != -1:
    content = text[s_idx + len(start_marker):e_idx]
    print(f"Length of _INSTRUMENTS_HTML: {len(content)}")
    print("First 1500 chars:\n", content[:1500])
else:
    print(f"Could not locate _INSTRUMENTS_HTML: s_idx={s_idx}, e_idx={e_idx}")
