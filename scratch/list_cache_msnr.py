import os

files = [f for f in os.listdir('data/cache_msnr') if 'Index' in f]
print("Index files in data/cache_msnr:")
for f in sorted(files)[:25]:
    print(f"  {f} ({os.path.getsize(os.path.join('data/cache_msnr', f)):,} bytes)")
