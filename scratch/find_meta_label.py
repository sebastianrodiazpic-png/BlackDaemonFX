with open('strategy/execution/live_trading_engine.py', 'r', encoding='utf-8', errors='ignore') as f:
    for idx, line in enumerate(f):
        if 'meta_label' in line and ('[' in line or '=' in line or 'dict' in line):
            print(f"{idx+1}: {line.strip()[:100]}")
