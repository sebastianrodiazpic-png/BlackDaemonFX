with open('dashboard/realtime_dashboard.py', 'r', encoding='utf-8', errors='ignore') as f:
    for idx, line in enumerate(f):
        if '"recent":' in line or "'recent':" in line or "balanced_recent" in line or "_recent_analyses" in line:
            print(f"{idx+1}: {line.strip()[:100]}")
