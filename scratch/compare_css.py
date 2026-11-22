# -*- coding: utf-8 -*-
with open("dashboard/realtime_dashboard.py", "r", encoding="utf-8") as f:
    text = f.read()

# Buscar en la primera página (dashboard principal) las reglas de .top, .title, .sub, .badge
import re
part1 = text[:text.find('<main class="wrap">')]

print("CSS rules in part 1:")
for r in ['.top', '.title', '.sub', '.badge', '.wrap']:
    m = re.findall(rf'{re.escape(r)}\b[^{{]*\{{[^}}]*\}}', part1)
    print(r, "->", m[:2])
