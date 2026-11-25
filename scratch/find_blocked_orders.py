import os

log_dir = 'storage/logs/bots'
for fname in os.listdir(log_dir):
    if not fname.endswith('.log'):
        continue
    fpath = os.path.join(log_dir, fname)
    with open(fpath, 'r', encoding='utf-8', errors='ignore') as f:
        for lnum, line in enumerate(f):
            if any(term in line for term in ['ORDER_SEND_BLOCKED_TERMINAL_DUPLICATE', 'ORDER_SEND_BLOCKED_ACTIVE_POSITION', 'TERMINAL_LOCK_TIMEOUT']):
                print(f"[{fname}:{lnum+1}] {line.strip()[:180]}")
