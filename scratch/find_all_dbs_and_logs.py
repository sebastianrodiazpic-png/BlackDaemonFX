import os, glob

print("=== ALL SQLITE / DB FILES ===")
for p in glob.glob("**/*.sqlite*", recursive=True) + glob.glob("**/*.db", recursive=True):
    size = os.path.getsize(p)
    print(f"  {p}: {size:,} bytes")

print("\n=== LOG FILES ===")
log_files = glob.glob("logs/**/*.log", recursive=True) + glob.glob("logs/*.log")
log_files = sorted(set(log_files), key=lambda x: os.path.getmtime(x), reverse=True)
print(f"Total log files: {len(log_files)}")
for lf in log_files[:20]:
    mtime = os.path.getmtime(lf)
    size = os.path.getsize(lf)
    print(f"  {lf} ({size:,} bytes, mtime={mtime})")
