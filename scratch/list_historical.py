import os

files = [f for f in os.listdir('data/historical') if f.endswith('.csv')]
print("Files in data/historical:")
for f in sorted(files):
    print(f"  {f} ({os.path.getsize(os.path.join('data/historical', f)):,} bytes)")
