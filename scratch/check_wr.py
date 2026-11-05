import pandas as pd
import json

df = pd.read_csv("storage/analysis/replay_synthetics_human_criteria_comparison.csv")
for st, grp in df.groupby("strategy"):
    print(f"=== Strategy: {st} ===")
    gt51 = grp[grp["pct_win_despues"] > 51.0]
    print(f"Count with WR > 51%: {len(gt51)} / {len(grp)}")
    for _, r in gt51.iterrows():
        print(f"  {r['symbol']}: WR={r['pct_win_despues']:.2f}%, R={r['r_despues']:.2f}")

print("\n=== Now checking MSNR_ACIERTO47_SYNTHETICS in ict_instrument_policy.py ===")
from config.ict_instrument_policy import MSNR_ACIERTO47_SYNTHETICS, ICT_FOREX_ACTIVE_BASES, ICT_MARKETS_ACTIVE, ICT_SYNTHETIC_FAMILIES
print("MSNR_ACIERTO47_SYNTHETICS:", len(MSNR_ACIERTO47_SYNTHETICS))
for s in MSNR_ACIERTO47_SYNTHETICS:
    print(" ", s)

print("\n=== ICT_FOREX_ACTIVE_BASES ===")
print("ICT_FOREX_ACTIVE_BASES:", len(ICT_FOREX_ACTIVE_BASES))
for s in ICT_FOREX_ACTIVE_BASES:
    print(" ", s)

print("\n=== ICT_MARKETS_ACTIVE ===")
print("ICT_MARKETS_ACTIVE:", len(ICT_MARKETS_ACTIVE))
for s in ICT_MARKETS_ACTIVE:
    print(" ", s)
