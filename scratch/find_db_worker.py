import sqlite3
import os

for root, dirs, files in os.walk('.'):
    if any(x in root for x in ['.git', 'venv', '.venv']):
        continue
    for f in files:
        if f.endswith(('.db', '.sqlite', '.sqlite3')):
            p = os.path.join(root, f)
            try:
                c = sqlite3.connect(p)
                for (t,) in c.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall():
                    try:
                        for row in c.execute(f'SELECT * FROM [{t}]').fetchall():
                            s = str(row)
                            if '26082032' in s or 'Metales' in s or '17628' in s:
                                print(f"{p} [{t}]: {s[:160]}")
                    except Exception:
                        pass
                c.close()
            except Exception:
                pass
