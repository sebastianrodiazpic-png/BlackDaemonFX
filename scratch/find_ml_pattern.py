import os

pattern = 'net_expectancy_r'
matches = []

for folder in ['app', 'strategy', 'services', 'risk', 'config']:
    for root, dirs, files in os.walk(folder):
        for file in files:
            if file.endswith('.py'):
                fpath = os.path.join(root, file)
                try:
                    with open(fpath, 'r', encoding='utf-8', errors='ignore') as f:
                        for line_no, line in enumerate(f, 1):
                            if pattern in line:
                                matches.append((fpath, line_no, line.strip()))
                except Exception:
                    pass

print(f"Total matches: {len(matches)}")
for m in matches:
    print(f"{m[0]}:{m[1]} -> {m[2]}")
