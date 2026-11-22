with open('strategy/execution/live_trading_engine.py', 'r', encoding='utf-8', errors='ignore') as f:
    for idx, line in enumerate(f):
        if "signal.get('strategy_name')" in line or 'signal.get("strategy_name")' in line:
            print(f"{idx+1}: {line.strip()[:100]}")
