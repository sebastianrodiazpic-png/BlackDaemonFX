import glob
import os

logs = [
    'storage/logs/bots/malaysian_snr.log',
    'storage/logs/bots/volatility_1.log',
    'storage/logs/bots/ict.log',
    'storage/logs/bots/orb.log',
    'storage/logs/bots/forex_1.log',
    'storage/logs/bots/step.log',
    'storage/logs/bots/jump.log',
    'storage/logs/bots/boom.log',
    'storage/logs/bots/crash.log',
]

for log_path in logs:
    if not os.path.exists(log_path):
        continue
    print(f"\n=======================================================")
    print(f"=== LOG: {log_path} (Size: {os.path.getsize(log_path)} bytes) ===")
    print(f"=======================================================")
    with open(log_path, 'r', encoding='utf-8', errors='ignore') as f:
        lines = f.readlines()
        tail = lines[-35:]
        for line in tail:
            print(line.rstrip())
