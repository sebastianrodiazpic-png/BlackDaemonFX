# -*- coding: utf-8 -*-
with open("dashboard/strategy_bases_page.py", "r", encoding="utf-8") as f:
    lines = f.readlines()

start_idx = None
end_idx = None
for i, l in enumerate(lines):
    if 'id="trendPullbackAuditPanel"' in l:
        start_idx = i
    if start_idx is not None and i > start_idx:
        if '</section>' in l or '<!--' in l and 'PANEL' in l:
            end_idx = i
            break

print(f"start: {start_idx}, end: {end_idx}")
if start_idx and end_idx:
    print(''.join(lines[start_idx:start_idx+35]))
    print("...")
    print(''.join(lines[end_idx-15:end_idx+5]))
