import sys
sys.path.insert(0, ".")
import os
import json
from strategy.orb.new_york_orb import NewYorkORBStrategy
from brokers.mt5_data import MT5DataProvider

provider = MT5DataProvider()
orb = NewYorkORBStrategy(data_provider=provider)

for sym in ["US SP 500", "US Tech 100"]:
    print("=" * 80)
    print("ANALYZING:", sym)
    try:
        res = orb.analyze_symbol(sym)
        # remove pandas objects for clean json dump
        clean_res = {}
        for k, v in res.items():
            if k == "orb_audit":
                clean_res[k] = {ak: av for ak, av in v.items() if ak != "opening_candles"}
            else:
                clean_res[k] = v
        print(json.dumps(clean_res, indent=2, default=str))
    except Exception as e:
        print("Error:", e)
