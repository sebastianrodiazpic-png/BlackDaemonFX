import subprocess, sys
sys.stdout.reconfigure(encoding='utf-8')

res = subprocess.run(['git', 'show', '3727624:dashboard/strategy_bases_page.py'], capture_output=True, text=True, encoding='utf-8')
lines = res.stdout.splitlines()

for i in range(310, 420):
    print(f"{i+1:04d}: {lines[i]}")
