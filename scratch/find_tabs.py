with open('dashboard/realtime_dashboard.py', 'r', encoding='utf-8', errors='ignore') as f:
    lines = f.readlines()

for i, l in enumerate(lines):
    if any(k in l for k in ['worker-tab', 'tab-button', 'data-tab', 'CARRY', 'GOLD', 'DRIFT', 'NIGHT', 'RSI2', 'MSNR']):
        if any(w in l for w in ['<button', '<nav', 'class="tab', 'class="nav', 'render_worker', 'workers_list', 'WORKERS']):
            print(f'{i+1}: {l.strip()[:100]}')
