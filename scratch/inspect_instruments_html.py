import sys

sys.stdout.reconfigure(encoding='utf-8')

with open('dashboard/realtime_dashboard.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

print("=== Around line 33823 ===")
for i in range(33815, 33850):
    if i < len(lines):
        print(f"L{i+1}: {lines[i]}", end='')

print("\n=== Around line 36146 ===")
for i in range(36140, 36160):
    if i < len(lines):
        print(f"L{i+1}: {lines[i]}", end='')
