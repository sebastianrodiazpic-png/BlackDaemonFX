with open('config/strategy_config.py', encoding='utf-8') as f:
    lines = f.readlines()

for i, l in enumerate(lines):
    if '"ICT":' in l:
        print(f'{i+1}: {l.strip()}')
        for j in range(i, i+10):
            print(f'{j+1}: {lines[j].strip()}')
