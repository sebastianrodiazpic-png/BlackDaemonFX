import glob, re
test_files = glob.glob('tests/**/*.py', recursive=True)
for path in test_files:
    with open(path, encoding='utf-8') as f:
        lines = f.readlines()
    for i, l in enumerate(lines, 1):
        if 'sabri' in l.lower() and ('assert' in l or '==' in l or 'in ' in l or 'self.' in l):
            print(f"{path}:{i}: {l.strip()}")
