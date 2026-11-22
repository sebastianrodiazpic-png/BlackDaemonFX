import glob, re
test_files = glob.glob('tests/**/*.py', recursive=True)
count = 0
for path in test_files:
    with open(path, encoding='utf-8') as f:
        text = f.read()
    m = re.findall(r'ICT Sabri Malle', text)
    if m:
        count += len(m)
        print(path, len(m))
print('Total matches of exact "ICT Sabri Malle" in tests:', count)
