import os

tickets = ['4797135661', '4796921802', '4796765886', '4796980220', '4796697303']
symbols = ['Volatility 30 (1s)', 'Boom 1000', 'Volatility 75']

log_dir = 'storage/logs/bots'
for fname in os.listdir(log_dir):
    if not fname.endswith('.log'):
        continue
    fpath = os.path.join(log_dir, fname)
    try:
        with open(fpath, 'r', encoding='utf-8', errors='ignore') as f:
            for lnum, line in enumerate(f):
                for t in tickets:
                    if t in line:
                        print(f"[{fname}:{lnum+1}] TICKET {t}: {line.strip()[:180]}")
    except Exception as e:
        print(f"Error reading {fname}: {e}")
