with open('strategy/execution/live_trading_engine.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

for j in range(10080, 10115):
    print(f'{j}: {lines[j]}', end='')
