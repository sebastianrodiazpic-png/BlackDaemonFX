with open('app/main.py', 'r', encoding='utf-8', errors='ignore') as f:
    lines = f.readlines()

for i, l in enumerate(lines):
    if 'BOT_PROFILES' in l or 'MULTI_BOT_DEFAULT_PROFILES' in l:
        print(f'{i+1}: {l.strip()[:100]}')
