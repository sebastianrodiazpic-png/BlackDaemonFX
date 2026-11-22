import os

patterns = ['ICT (Metales', 'Metales, Cripto &', 'Metales, Cripto']
for root, dirs, files in os.walk('.'):
    if any(x in root for x in ['.venv', '.git', 'graphify-out', '.pytest_cache', '__pycache__', 'reports']):
        continue
    for f in files:
        if f.endswith(('.py', '.html', '.js', '.json', '.md', '.ts')):
            p = os.path.join(root, f)
            try:
                with open(p, 'r', encoding='utf-8', errors='ignore') as fh:
                    for i, line in enumerate(fh, 1):
                        for pat in patterns:
                            if pat.lower() in line.lower():
                                print(f'{p}:{i}: {line.strip()[:140]}')
            except Exception:
                pass
