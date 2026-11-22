with open('strategy/execution/live_trading_engine.py', encoding='utf-8') as f:
    lines = f.readlines()

for idx, line in enumerate(lines, 1):
    if 'sabri' in line.lower():
        print(f"{idx}: {line.strip()[:120]}")
