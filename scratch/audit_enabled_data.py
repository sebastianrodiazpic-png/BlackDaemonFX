import sys
from pathlib import Path
import pandas as pd
import json

ROOT = Path("c:/TradingBoot/smc_synthetic_bot")

enabled_symbols = {
    "MSNR": ['Crash 500 Index', 'Crash 600 Index', 'Crash 1000 Index', 'Boom 1000 Index', 'Boom 500 Index', 'Boom 300 Index', 'Step Index', 'Step Index 400', 'Wall Street 30', 'XAUUSD', 'EURUSD', 'GBPUSD', 'USDJPY', 'GBPJPY', 'GBPAUD', 'Jump 10 Index', 'Jump 25 Index', 'Jump 50 Index', 'BTCUSD'],
    "ICT": ['XAUUSD', 'XAUUSDmicro', 'Jump 50 Index', 'EURUSD', 'EURUSDmicro', 'Crash 300 Index', 'Boom 500 Index', 'Boom 300 Index', 'Boom 1000 Index', 'Boom 600 Index', 'Jump 25 Index', 'BTCUSD', 'Step Index 400', 'Wall Street 30', 'US Tech 100', 'US SP 500', 'XAGUSD', 'XAGUSDmicro'],
    "ORB": ['Wall Street 30', 'XAUUSD', 'XAUUSDmicro', 'US Tech 100', 'BTCUSD'],
    "GOLD_QUARTERS": ['XAUUSD', 'XAUUSDmicro', 'microXAUUSD']
}

all_needed = set()
for s_list in enabled_symbols.values():
    all_needed.update(s_list)

print(f"Total unique enabled symbols across all 4 strategies: {len(all_needed)}")

# Find all data files in ROOT
data_dirs = [ROOT / "data", ROOT / "storage/analysis"]
found_data = {}

for d in data_dirs:
    if not d.exists(): continue
    for p in d.rglob("*"):
        if ".graphify" in p.parts: continue
        if p.is_file() and p.suffix.lower() in [".csv", ".pkl"]:
            # extract potential symbol name
            stem = p.stem
            # check which symbol it matches
            for sym in all_needed:
                clean_sym = sym.replace(" ", "_")
                if clean_sym.lower() in stem.lower() or sym.lower() in stem.lower():
                    tf = "M5" if "_M5" in stem else "M15" if "_M15" in stem else "H1" if "_H1" in stem else "D1" if "_D1" in stem else "OTHER"
                    found_data.setdefault(sym, []).append({
                        "file": str(p.relative_to(ROOT)),
                        "tf": tf,
                        "size_mb": p.stat().st_size / (1024*1024)
                    })

print("\n--- DATA AUDIT PER ENABLED SYMBOL ---")
for sym in sorted(all_needed):
    files = found_data.get(sym, [])
    if files:
        print(f"\nSymbol: {sym:25s} (Found {len(files)} files)")
        for f in files[:4]:
            print(f"   {f['tf']:5s} | {f['size_mb']:5.2f} MB | {f['file']}")
    else:
        print(f"\nSymbol: {sym:25s} | NO LOCAL HISTORICAL FILE FOUND")
