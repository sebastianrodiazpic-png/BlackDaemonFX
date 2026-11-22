with open('config/ict_instrument_policy.py', encoding='utf-8') as f:
    lines = f.readlines()

for i, l in enumerate(lines):
    if 'INDICESB_SNR' in l:
        print(f'{i+1}: {l.strip()[:100]}')
        for j in range(max(0, i-2), min(len(lines), i+8)):
            print(f'  {j+1}: {lines[j].rstrip()}')
