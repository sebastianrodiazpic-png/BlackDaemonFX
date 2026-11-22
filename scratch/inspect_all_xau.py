import pandas as pd
from pathlib import Path
import json

ROOT = Path(".")
OUT_DIR = ROOT / "storage" / "analysis"

signal_files = [
    "newsyn_y0b.csv", "newsyn_y1.csv", "synth_free_y0b.csv", "synth_free_y1.csv",
    "y0.csv", "y1.csv", "prereg_D_2024.csv",
    "cmp_alch_A.csv", "cmp_alch_B.csv", "cmp_alch_D.csv",
    "real_win_asia_A.csv", "real_win_asia_B.csv", "real_win_asia_D.csv",
    "real_win_legacy_A.csv", "real_win_legacy_B.csv", "real_win_legacy_D.csv",
    "real_e1_A.csv", "real_e1_B.csv", "real_e1_D.csv"
]

dfs = []
for fname in signal_files:
    fpath = OUT_DIR / f"msnr_variants_signals_{fname}"
    if fpath.exists():
        try:
            df = pd.read_csv(fpath)
            xau = df[df['symbol'] == 'XAUUSD'].copy()
            if len(xau) > 0:
                xau['source_file'] = fname
                dfs.append(xau)
        except Exception as e:
            pass

if dfs:
    all_xau = pd.concat(dfs, ignore_index=True)
    print(f"Total XAU signals across all variant files: {len(all_xau)}")
    print(all_xau[['source_file', 'time', 'direction', 'rr_live']].head(15))
    
    # Check unique trades
    all_xau_unique = all_xau.drop_duplicates(subset=['time'])
    print(f"Unique XAU signals: {len(all_xau_unique)}")
    if 'rr_live' in all_xau_unique.columns:
        wins = (all_xau_unique['rr_live'] > 0).sum()
        losses = (all_xau_unique['rr_live'] < 0).sum()
        total = len(all_xau_unique)
        wr = (wins / total * 100) if total > 0 else 0
        net_r = all_xau_unique['rr_live'].sum()
        print(f"Unique XAU: {total} trades, {wins} wins, {losses} losses, WR: {wr:.2f}%, Net R: {net_r:+.2f}R")
