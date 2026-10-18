import sys
from pathlib import Path

log_path = Path("storage/logs/bots/malaysian_snr.log")
if not log_path.exists():
    print(f"Log not found at {log_path}")
    sys.exit(0)

size_mb = log_path.stat().st_size / (1024 * 1024)
print(f"Log size: {size_mb:.2f} MB")

# Read last 500 lines
with open(log_path, "r", encoding="utf-8", errors="ignore") as f:
    f.seek(max(0, log_path.stat().st_size - 100000)) # last ~100KB
    lines = f.readlines()

print(f"\nLast {min(50, len(lines))} lines of malaysian_snr.log:")
for l in lines[-50:]:
    print(l.strip())

# Count occurrences of key rejection phrases in the last 2000 lines
with open(log_path, "r", encoding="utf-8", errors="ignore") as f:
    f.seek(max(0, log_path.stat().st_size - 1000000)) # last ~1MB
    recent_lines = f.readlines()

from collections import Counter
rejection_counter = Counter()
for l in recent_lines:
    if any(k in l for k in ['BLOCKED', 'REJECT', 'DISCARD', 'EXPIRED', 'SKIP', 'DROP', 'ai_filter', 'EXPECTANCY', 'PROBABILITY']):
        # extract short summary
        rejection_counter[l.strip()[:100]] += 1

print("\n--- Recent Rejections / Filter events in last 1MB ---")
for msg, count in rejection_counter.most_common(20):
    print(f"[{count}x] {msg}")
