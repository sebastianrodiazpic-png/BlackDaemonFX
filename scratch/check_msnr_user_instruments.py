import sys
sys.path.insert(0, ".")
from dashboard.strategy_bases_page import STRATEGY_DATA

msnr_data = STRATEGY_DATA.get("msnr", {})
instruments = msnr_data.get("instruments", [])
print(f"Total MSNR instruments in STRATEGY_DATA: {len(instruments)}")
for item in instruments:
    sym = item.get("symbol") or item.get("instrument") or ""
    if any(k.lower() in sym.lower() for k in ["usdchf", "audcad", "germany", "audusd", "vol over", "crash 550", "boom 550", "ger40"]):
        print(f"{sym}: WR={item.get('win_rate')}%, R={item.get('return_r')} R, trades={item.get('trades')}, pruned={item.get('pruned')}")
