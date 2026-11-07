import os
from pathlib import Path

for root, dirs, files in os.walk('.'):
    if '.git' in dirs:
        dirs.remove('.git')
    for f in files:
        if f.endswith(('.py', '.js', '.html')):
            p = Path(root) / f
            try:
                txt = p.read_text(encoding='utf-8')
                if 'La carga está tardando' in txt or 'tardando más de lo habitual' in txt:
                    print(f"Found in: {p}")
            except Exception:
                pass
