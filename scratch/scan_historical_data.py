from pathlib import Path
import os

ROOT = Path("c:/TradingBoot/smc_synthetic_bot")

print("=== CHECKING HISTORICAL DATA FILES IN PROJECT ===")

def scan_dir(dir_name):
    d = ROOT / dir_name
    if not d.exists():
        print(f"Directory {dir_name} does not exist.")
        return
    print(f"\nScanning {dir_name}:")
    files = []
    for p in d.rglob("*"):
        if ".graphify" in p.parts:
            continue
        if p.is_file() and p.suffix.lower() in [".csv", ".parquet", ".pkl", ".sqlite3", ".json", ".feather"]:
            files.append(p)
    print(f"Total relevant data files in {dir_name}: {len(files)}")
    for f in sorted(files, key=lambda x: x.stat().st_size, reverse=True)[:25]:
        print(f"  {f.relative_to(ROOT)} | {f.stat().st_size / (1024*1024):.2f} MB")

scan_dir("storage")
scan_dir("marketdata")
scan_dir("data")

appdata_md = Path(r"C:\Users\sebas\AppData\Local\BlackDaemonFx\market_data")
if appdata_md.exists():
    print(f"\nScanning AppData market_data:")
    ad_files = list(appdata_md.glob("*"))
    print(f"Total files in AppData market_data: {len(ad_files)}")
    for f in sorted(ad_files, key=lambda x: x.stat().st_size, reverse=True)[:15]:
        print(f"  {f.name} | {f.stat().st_size / (1024*1024):.2f} MB")
