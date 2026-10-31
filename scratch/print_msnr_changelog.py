import sys
sys.stdout.reconfigure(encoding='utf-8')

with open('REGISTRO_CAMBIOS_ESTRATEGIA.md', 'r', encoding='utf-8') as f:
    lines = f.readlines()

for i, line in enumerate(lines):
    if '###' in line and ('msnr' in line.lower() or 'malaysian' in line.lower()):
        print(f"Line {i+1}: {line.strip()}")
        # print next 25 lines
        for j in range(i+1, min(i+25, len(lines))):
            if lines[j].startswith('###'):
                break
            print("  " + lines[j].strip())
        print("-" * 60)
