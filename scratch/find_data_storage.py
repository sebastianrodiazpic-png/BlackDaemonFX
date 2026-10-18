from pathlib import Path

print("--- Data files under storage/analysis and data/ ---")
for p in Path("storage").rglob("*.*"):
    if p.suffix in ['.csv', '.parquet', '.sqlite3', '.db']:
        mb = p.stat().st_size / (1024 * 1024)
        if mb > 0.05:
            print(f"{p.as_posix()}: {mb:.2f} MB")

data_dir = Path("data")
if data_dir.exists():
    for p in data_dir.rglob("*.*"):
        mb = p.stat().st_size / (1024 * 1024)
        print(f"{p.as_posix()}: {mb:.2f} MB")
else:
    print("data/ directory does not exist.")
