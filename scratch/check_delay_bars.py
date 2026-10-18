import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import sqlite3
import json
import pandas as pd

db_path = Path("storage/runtime/shadow_research_staging.sqlite3")
arch_dir = Path("storage/runtime/m1_prospective_cache")

from tools.prospective_m1_replay_runner import ProspectiveM1ReplayRunner
runner = ProspectiveM1ReplayRunner(db_path=db_path, dry_run=True, archive_dir=arch_dir)
runner.fetch_market_data(["Boom 500 Index", "Crash 300 Index", "Boom 600 Index", "Jump 10 Index", "Crash 600 Index", "Boom 300 Index"])

conn = sqlite3.connect(f"file:{db_path.resolve()}?mode=ro", uri=True)
df = pd.read_sql_query("SELECT * FROM shadow_signals WHERE variant IN ('base', 'enabled_19_h4_fresh') AND timestamp >= '2026-10-15T17:35:16.304722+00:00'", conn)
conn.close()

print("=== AUDIT OF BARS BETWEEN signal_time AND created_at ===")
for _, r in df.iterrows():
    feat = json.loads(r["features_json"]) if r["features_json"] else {}
    sig_t = pd.to_datetime(r["timestamp"], utc=True)
    cre_t = pd.to_datetime(feat.get("created_at_live", r["timestamp"]), utc=True)
    bars = runner.cache_m1[r["symbol"]]
    
    # Bars between sig_t and cre_t
    between = bars[(bars["time"] >= sig_t) & (bars["time"] < cre_t)]
    min_low = between["low"].min() if not between.empty else None
    max_high = between["high"].max() if not between.empty else None
    
    sl = r["stop_loss"]
    tp1 = r["take_profit_1"]
    dir_ = r["direction"]
    
    sl_hit_during_delay = False
    tp1_hit_during_delay = False
    if not between.empty:
        if dir_ == "BUY":
            if min_low <= sl:
                sl_hit_during_delay = True
            if max_high >= tp1:
                tp1_hit_during_delay = True
        elif dir_ == "SELL":
            if max_high >= sl:
                sl_hit_during_delay = True
            if min_low <= tp1:
                tp1_hit_during_delay = True
            
    print(f"ID {r['id']:<2} | {r['strategy']:<4} | {r['symbol']:<16} {dir_} | Sig: {str(sig_t)[11:19]} -> Cre: {str(cre_t)[11:19]} ({len(between)} bars)")
    print(f"      SL={sl:.2f}, TP1={tp1:.2f} | Low={min_low}, High={max_high}")
    print(f"      Hit SL during delay? {sl_hit_during_delay} | Hit TP1 during delay? {tp1_hit_during_delay}")

if __name__ == "__main__":
    pass
