# -*- coding: utf-8 -*-
with open("dashboard/realtime_dashboard.py", "r", encoding="utf-8") as f:
    text = f.read()

import re
matches = [m.start() for m in re.finditer(r'<main\b[^>]*>', text)]
idx = matches[0]
print(text[idx:idx+1500])
