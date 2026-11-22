import pandas as pd
from pathlib import Path

OUT = Path("storage/analysis")

for tag in ["real_win_legacy_A", "real_win_legacy_B", "real_win_legacy_D", "real_win_asia_A", "real_win_asia_B", "real_win_asia_D"]:
    p = OUT / f"msnr_variants_signals_{tag}.csv"
    if p.exists():
        df = pd.read_csv(p)
        xau = df[df['symbol'] == 'XAUUSD']
        print(f"File {tag}: Total rows={len(df)}, XAUUSD rows={len(xau)}")
        if len(xau) > 0:
            # Let's inspect winrate and rr_live if available
            cols = [c for c in ['outcome', 'rr_live', 'pnl_r', 'win'] if c in xau.columns]
            print(f"   XAU columns: {cols}")
            if 'rr_live' in xau.columns:
                wins = (xau['rr_live'] > 0).sum()
                wr = (wins / len(xau)) * 100
                total_r = xau['rr_live'].sum()
                print(f"   XAUUSD: {len(xau)} trades, {wins} wins, WR: {wr:.1f}%, Net R: {total_r:+.2f}R")
