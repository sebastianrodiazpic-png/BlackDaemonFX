import os

target = 'FOREX_NEWS_TRAILING_PRESERVED'
for root, dirs, files in os.walk('.'):
    if any(p in root for p in ['.venv', '.git', 'graphify-out', '.test_tmp']):
        continue
    for f in files:
        if f.endswith('.py'):
            p = os.path.join(root, f)
            with open(p, 'r', encoding='utf-8', errors='ignore') as fp:
                for idx, line in enumerate(fp, 1):
                    if target in line:
                        print(f"{p}:{idx} -> {line.strip()}")
