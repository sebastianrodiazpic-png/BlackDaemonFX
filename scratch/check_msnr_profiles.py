with open('strategy/execution/live_trading_engine.py', 'r', encoding='utf-8', errors='ignore') as f:
    lines = f.readlines()

for idx, line in enumerate(lines):
    if 'bot_profile' in line and 'MALAYSIAN_SNR' in line:
        print(f"Line {idx+1}: {line.strip()}")
        # print 2 lines before and after
        for j in range(max(0, idx-2), min(len(lines), idx+3)):
            if j != idx:
                print(f"   {j+1}: {lines[j].strip()}")
        print("-" * 50)
