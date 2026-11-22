# -*- coding: utf-8 -*-
with open("dashboard/strategy_bases_page.py", "r", encoding="utf-8") as f:
    lines = f.readlines()

stack = []
for line_num, line in enumerate(lines, 1):
    import re
    tokens = re.finditer(r'(<div\b[^>]*>|</div>)', line)
    for m in tokens:
        t = m.group(1)
        if t.startswith('<div'):
            id_m = re.search(r'id=["\']([^"\']+)["\']', t)
            cls_m = re.search(r'class=["\']([^"\']+)["\']', t)
            info = id_m.group(1) if id_m else (cls_m.group(1) if cls_m else "div")
            stack.append((line_num, info))
        elif t == '</div>':
            if stack:
                popped = stack.pop()
            else:
                print(f"Extra closing div at line {line_num}")
    if line_num == 4660:
        print("Stack at line 4660:", [(l, inf) for l, inf in stack])
        break
