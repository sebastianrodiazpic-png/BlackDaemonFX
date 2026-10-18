import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import sqlite3
import json
import pandas as pd
from tools.prospective_m1_replay_runner import ProspectiveM1ReplayRunner, TYPICAL_SPREADS

db_path = Path("storage/runtime/shadow_research_staging.sqlite3")
arch_dir = Path("storage/runtime/m1_prospective_cache")
runner = ProspectiveM1ReplayRunner(db_path=db_path, dry_run=True, archive_dir=arch_dir)
symbols = ["Boom 500 Index", "Crash 300 Index", "Boom 600 Index", "Jump 10 Index", "Crash 600 Index", "Boom 300 Index"]
runner.fetch_market_data(symbols)

conn = sqlite3.connect(f"file:{db_path.resolve()}?mode=ro", uri=True)
df = pd.read_sql_query("SELECT * FROM shadow_signals WHERE variant IN ('base', 'enabled_19_h4_fresh') AND timestamp >= '2026-10-15T17:35:16.304722+00:00'", conn)
conn.close()

print("=" * 80)
print("FORENSIC AUDIT: BARS BETWEEN signal_time AND created_at")
print("=" * 80)

for _, row in df.iterrows():
    sid = row["id"]
    strat = row["strategy"]
    sym = row["symbol"]
    dir_ = row["direction"]
    spread = TYPICAL_SPREADS.get(sym, 0.0)
    
    feat = json.loads(row["features_json"]) if row["features_json"] else {}
    sig_t = pd.to_datetime(row["timestamp"], utc=True)
    cre_t = pd.to_datetime(feat.get("created_at_live", row["timestamp"]), utc=True)
    delay_sec = (cre_t - sig_t).total_seconds()
    delay_min = delay_sec / 60.0
    
    bars = runner.cache_m1[sym]
    between = bars[(bars["time"] >= sig_t) & (bars["time"] < cre_t)]
    
    ep = row["entry_price"]
    sl = row["stop_loss"]
    tp1 = row["take_profit_1"]
    tp2 = row["take_profit_2"]
    
    # Check if SL or TP1 or TP2 was breached during the delay window
    sl_breached_bar = None
    tp1_breached_bar = None
    tp2_breached_bar = None
    
    for _, b in between.iterrows():
        b_time = b["time"]
        b_high = float(b["high"]) + (spread if dir_ == "SELL" else 0.0)
        b_low = float(b["low"]) + (spread if dir_ == "SELL" else 0.0)
        
        if dir_ == "BUY":
            hit_sl = b_low <= sl
            hit_tp1 = b_high >= tp1
            hit_tp2 = b_high >= tp2
        else: # SELL
            hit_sl = b_high >= sl
            hit_tp1 = b_low <= tp1
            hit_tp2 = b_low <= tp2
            
        if hit_sl and sl_breached_bar is None:
            sl_breached_bar = (b_time, b_low if dir_ == "BUY" else b_high)
        if hit_tp1 and tp1_breached_bar is None:
            tp1_breached_bar = (b_time, b_high if dir_ == "BUY" else b_low)
        if hit_tp2 and tp2_breached_bar is None:
            tp2_breached_bar = (b_time, b_high if dir_ == "BUY" else b_low)
            
    print(f"\nID {sid:02d} | {strat} | {sym} {dir_}")
    print(f"  signal_time: {sig_t} | created_at: {cre_t} | Delay: {delay_min:.2f} min ({len(between)} bars)")
    print(f"  EP: {ep:.2f} | SL: {sl:.2f} | TP1: {tp1:.2f} | TP2: {tp2:.2f}")
    
    if sl_breached_bar or tp1_breached_bar:
        print(f"  --> LEVEL BREACHED DURING DELAY WINDOW:")
        if sl_breached_bar:
            print(f"      [SL HIT] Bar {sl_breached_bar[0]} reached {sl_breached_bar[1]:.4f} (SL={sl:.4f})")
        if tp1_breached_bar:
            print(f"      [TP1 HIT] Bar {tp1_breached_bar[0]} reached {tp1_breached_bar[1]:.4f} (TP1={tp1:.4f})")
        if tp2_breached_bar:
            print(f"      [TP2 HIT] Bar {tp2_breached_bar[0]} reached {tp2_breached_bar[1]:.4f} (TP2={tp2:.4f})")
            
        # Determine chronological priority if both were hit during delay
        if sl_breached_bar and tp1_breached_bar:
            if sl_breached_bar[0] < tp1_breached_bar[0]:
                print(f"      --> CHRONOLOGICAL PRIORITY: SL was breached FIRST at {sl_breached_bar[0]}")
            elif tp1_breached_bar[0] < sl_breached_bar[0]:
                print(f"      --> CHRONOLOGICAL PRIORITY: TP1 was breached FIRST at {tp1_breached_bar[0]}")
            else:
                print(f"      --> SAME BAR CONFLICT during delay at {sl_breached_bar[0]}: Conservative rule gives SL priority")
    else:
        print(f"  --> No levels breached during delay. Signal was still fully active at created_at.")
