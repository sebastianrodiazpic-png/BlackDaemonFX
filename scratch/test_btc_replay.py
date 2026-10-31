import sys
from pathlib import Path
import time
import json
import pandas as pd
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import tools.replay_orb_nunez_2y as R
from strategy.orb import new_york_orb as orb
from strategy.orb.asset_rules import ASSET_CONFIG, audit_volume_confirmation, check_range_amplitude
from tools.replay_orb_sweep_expanded import managed_simulator

df, cov = R.load("BTCUSD")
fetch_audit = json.loads((Path("storage/analysis/orb_sweep_expanded/fetch_audit.json")).read_text())
point = fetch_audit["BTCUSD"]["point"]

cfg = ASSET_CONFIG["BTCUSD"]
print("BTCUSD baseline cfg:", cfg)

START = pd.Timestamp("2024-10-03", tz="UTC")

def run_btc_replay(atr_multiple, req_volume=True, max_ny_min=690):
    trades = []
    skipped_amplitude = 0
    sessions_total = 0
    for day, group in df.groupby(df.ny_date, sort=True):
        if day.weekday() >= 5 or pd.Timestamp(day, tz="UTC") < START:
            continue
        minutes = group.ny_minute
        opening = group[(minutes >= 570) & (minutes < 585)]
        indices = group[(minutes >= 585) & (minutes < max_ny_min)].index.to_list()
        if len(opening) != 3 or set(opening.time_ny.dt.minute) != {30, 35, 40} or not indices:
            continue
        sessions_total += 1
        
        # Compute ATR(14)
        history_before_range = df[df.time_ny < opening.time_ny.iloc[-1]]
        if len(history_before_range) < 15:
            continue
        atr = orb.NewYorkORBStrategy._average_true_range(history_before_range, 14)
        if not atr:
            continue
        
        range_high, range_low = float(opening.high.max()), float(opening.low.min())
        amp = check_range_amplitude(range_high, range_low, atr, atr_multiple)
        if not amp["isValid"]:
            skipped_amplitude += 1
            continue
        
        # Look for sweep signal
        mid = (range_high + range_low) / 2.0
        buffer = cfg.get("atr_buffer", 0.05) * atr
        
        found_trade = False
        for offset, idx in enumerate(indices):
            bar = df.iloc[idx]
            for earlier in range(max(0, offset - 3), offset):
                sweep_idx = indices[earlier]
                sweep = df.iloc[sweep_idx]
                before = df.iloc[max(0, sweep_idx - 3):sweep_idx]
                if len(before) != 3 or not (range_low < float(sweep["close"]) < range_high):
                    continue
                sell = float(sweep["high"]) > range_high + buffer and float(bar["close"]) < min(float(before["low"].min()), mid)
                buy = float(sweep["low"]) < range_low - buffer and float(bar["close"]) > max(float(before["high"].max()), mid)
                if not sell and not buy:
                    continue
                direction = "SELL" if sell else "BUY"
                side = -1 if sell else 1
                evidence = audit_volume_confirmation(df.iloc[max(0, idx - 350):idx + 1], sweep["time"], "RETEST", req_volume)
                session = df.iloc[opening.index[0]:idx + 1]
                vwap = orb.NewYorkORBStrategy._session_vwap(session)
                poc = orb.NewYorkORBStrategy._session_poc(session)
                if not evidence["confirmed"] or not any(lvl is not None and side * (float(bar["close"]) - lvl) > 0 for lvl in (vwap, poc)):
                    continue
                structural_stop = float(sweep["high"]) + buffer if sell else float(sweep["low"]) - buffer
                
                # Simulate trade
                if idx + 1 >= len(df):
                    continue
                sim = managed_simulator(df, idx + 1, direction, structural_stop, point)
                if sim is not None:
                    trades.append({
                        "session_date": str(day),
                        "direction": direction,
                        "entry_time": sim["entry_time"],
                        "entry_price": sim["entry_price"],
                        "stop_loss": sim["stop_loss"],
                        "net_r": sim["net_r"],
                        "net_r_ext": sim["net_r_ext"],
                        "leg1_r": sim["leg1_r"],
                        "leg2_r": sim["leg2_r"],
                        "leg2_r_ext": sim["leg2_r_ext"],
                    })
                    found_trade = True
                    break
            if found_trade:
                break
    
    tdf = pd.DataFrame(trades)
    n = len(tdf)
    if n > 0:
        wr = (tdf["net_r_ext"] > 0).mean() * 100
        tot_r = tdf["net_r_ext"].sum()
        r_op = tdf["net_r_ext"].mean()
    else:
        wr, tot_r, r_op = 0, 0, 0
    return {
        "sessions": sessions_total,
        "skipped_amplitude": skipped_amplitude,
        "trades": n,
        "wr": wr,
        "tot_r": tot_r,
        "r_op": r_op,
    }

print("Running BTCUSD test...")
res_base = run_btc_replay(atr_multiple=1.8, req_volume=True, max_ny_min=690)
print("Baseline (1.8 ATR, Vol=True, Cutoff=11:30):", res_base)

res_relaxed_atr = run_btc_replay(atr_multiple=2.8, req_volume=True, max_ny_min=690)
print("Relaxed ATR (2.8 ATR, Vol=True, Cutoff=11:30):", res_relaxed_atr)

res_no_vol = run_btc_replay(atr_multiple=2.8, req_volume=False, max_ny_min=690)
print("Relaxed ATR + No Vol req (2.8 ATR, Vol=False, Cutoff=11:30):", res_no_vol)

res_full = run_btc_replay(atr_multiple=3.0, req_volume=False, max_ny_min=750)
print("Full Optimized (3.0 ATR, Vol=False, Cutoff=12:30):", res_full)
