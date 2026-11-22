with open('app/main.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

for j in range(1060, 1105):
    print(f'{j}: {lines[j]}', end='')
