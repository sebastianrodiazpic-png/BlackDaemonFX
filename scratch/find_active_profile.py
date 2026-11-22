with open('dashboard/realtime_dashboard.py', 'r', encoding='utf-8') as f:
    for i, line in enumerate(f, 1):
        if 'activeProfile' in line and any(k in line for k in ['var ', 'let ', 'const ', '=']):
            print(f"{i}: {line.strip()[:100]}")
