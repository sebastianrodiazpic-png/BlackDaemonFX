import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import sqlite3
import json
import pandas as pd
import numpy as np
from datetime import datetime, timezone
from marketdata.deriv import DerivMarketDataProvider

# Connect to staging DB in read-only mode
conn = sqlite3.connect("file:storage/runtime/shadow_research_staging.sqlite3?mode=ro", uri=True)
cur = conn.cursor()
cur.execute("""
    SELECT id, timestamp, strategy, variant, symbol, direction, entry_price, stop_loss, take_profit_1, take_profit_2, final_action, market_outcome, market_rr, features_json
    FROM shadow_signals
    ORDER BY timestamp ASC, id ASC
""")
rows = cur.fetchall()
conn.close()

# Group by event_uuid
events = {}
for r in rows:
    feat = json.loads(r[13]) if r[13] else {}
    ev_uuid = feat.get("event_uuid", f"{r[1]}_{r[2]}_{r[4]}_{r[5]}")
    if ev_uuid not in events:
        events[ev_uuid] = {
            "uuid": ev_uuid,
            "signal_time": r[1],
            "strategy": r[2],
            "symbol": r[4],
            "direction": r[5],
            "entry_price": r[6],
            "stop_loss": r[7],
            "take_profit_1": r[8],
            "take_profit_2": r[9],
            "source_id": feat.get("source_signal_id"),
            "market_outcome": r[11],
            "market_rr": r[12],
            "variants": {}
        }
    events[ev_uuid]["variants"][r[3]] = {
        "action": r[10],
        "sim_outcome": feat.get("simulated_outcome"),
        "sim_rr": feat.get("simulated_rr")
    }

print(f"Total Unique Events in Staging: {len(events)}")
cutoff_dt = pd.to_datetime("2026-10-15T17:35:16.304722+00:00", utc=True)

provider = DerivMarketDataProvider()

# Fetch 1000 M1 candles for all 6 symbols
cache_m1 = {}
symbols = list(set(ev["symbol"] for ev in events.values()))
print(f"Fetching M1 candles for {symbols}...")
for s in symbols:
    df = provider.get_candles(s, timeframe="M1", count=1000)
    cache_m1[s] = df
    print(f"  {s}: {len(df)} candles, from {df['time'].min()} to {df['time'].max()}")

print("\n" + "="*80)
print("INDEPENDENT M1 FORWARD REPLAY ANALYSIS")
print("="*80)

for ev_uuid, ev in events.items():
    sig_time = pd.to_datetime(ev["signal_time"], utc=True)
    is_prospect = sig_time >= cutoff_dt
    tag = "PROSPECTIVE" if is_prospect else "PRE_CUTOFF"
    sym = ev["symbol"]
    direction = ev["direction"]
    sig_entry = ev["entry_price"]
    sl = ev["stop_loss"]
    tp1 = ev["take_profit_1"]
    tp2 = ev["take_profit_2"] if ev["take_profit_2"] is not None else tp1
    
    df_m1 = cache_m1.get(sym)
    if df_m1 is None or df_m1.empty:
        print(f"[{tag}] {ev_uuid}: NO M1 DATA")
        continue
    
    # Filter bars after signal_time
    future_bars = df_m1[df_m1["time"] > sig_time].copy().reset_index(drop=True)
    if future_bars.empty:
        print(f"[{tag}] {ev_uuid}: NO BARS AFTER SIGNAL_TIME ({sig_time})")
        continue
    
    # Entry fill is the OPEN of the first bar after signal
    fill_time = future_bars["time"].iloc[0]
    fill_price = future_bars["open"].iloc[0]
    
    risk = abs(fill_price - sl)
    sign = 1 if direction == "BUY" else -1
    
    # Check if risk is valid
    if (direction == "BUY" and sl >= fill_price) or (direction == "SELL" and sl <= fill_price) or risk <= 0:
        print(f"[{tag}] {ev_uuid}: INVALID RISK fill={fill_price}, sl={sl}")
        continue
        
    # Standard rule:
    # TP1 is 2R from fill, Runner is 4R from fill (or structural if specified)
    # Let's check if the signal had predefined TP1/TP2 or if we use 2R / 4R:
    # In live faithful replay: tp1 = fill + sign * 2.0 * risk, tp2 = fill + sign * 4.0 * risk (or signal tp1/tp2)
    # Let's compute both: exact signal TP and fixed 2R/4R
    tp1_target = fill_price + sign * 2.0 * risk
    tp2_target = fill_price + sign * 4.0 * risk
    
    # Trace minute by minute
    leg1_done = False
    leg1_exit_bar = None
    leg1_rr = 0.0
    leg1_exit_reason = None
    
    leg2_done = False
    leg2_exit_bar = None
    leg2_rr = 0.0
    leg2_exit_reason = None
    
    active_sl_leg2 = sl
    
    for idx, row in future_bars.iterrows():
        b_time = row["time"]
        b_open = row["open"]
        b_high = row["high"]
        b_low = row["low"]
        b_close = row["close"]
        
        # Check Leg 1
        if not leg1_done:
            # Conservative: check SL first
            if direction == "BUY":
                hit_sl = b_low <= sl
                hit_tp1 = b_high >= tp1_target
            else:
                hit_sl = b_high >= sl
                hit_tp1 = b_low <= tp1_target
                
            if hit_sl and hit_tp1:
                # Same bar touch -> SL wins
                leg1_done = True
                leg1_rr = -1.0
                leg1_exit_reason = "SL_SAME_BAR_CONFLICT"
                leg1_exit_bar = idx
                # Leg 2 also stopped
                leg2_done = True
                leg2_rr = -1.0
                leg2_exit_reason = "SL_SAME_BAR_CONFLICT"
                leg2_exit_bar = idx
                break
            elif hit_sl:
                leg1_done = True
                leg1_rr = -1.0
                leg1_exit_reason = "SL"
                leg1_exit_bar = idx
                leg2_done = True
                leg2_rr = -1.0
                leg2_exit_reason = "SL"
                leg2_exit_bar = idx
                break
            elif hit_tp1:
                leg1_done = True
                leg1_rr = 2.0
                leg1_exit_reason = "TP1"
                leg1_exit_bar = idx
                # Leg 2 moves SL to Breakeven (fill_price)
                active_sl_leg2 = fill_price
                
        # Check Leg 2 if Leg 1 hit TP1
        if leg1_done and not leg2_done:
            if direction == "BUY":
                hit_be = b_low <= active_sl_leg2
                hit_tp2 = b_high >= tp2_target
            else:
                hit_be = b_high >= active_sl_leg2
                hit_tp2 = b_low <= tp2_target
                
            if hit_be and hit_tp2:
                # Same bar touch -> BE wins
                leg2_done = True
                leg2_rr = 0.0
                leg2_exit_reason = "BE_SAME_BAR"
                leg2_exit_bar = idx
                break
            elif hit_be:
                leg2_done = True
                leg2_rr = 0.0
                leg2_exit_reason = "BE"
                leg2_exit_bar = idx
                break
            elif hit_tp2:
                leg2_done = True
                leg2_rr = 4.0
                leg2_exit_reason = "TP2"
                leg2_exit_bar = idx
                break
                
    # If still open at end of available bars
    if not leg1_done:
        last_c = future_bars["close"].iloc[-1]
        unrealized = sign * (last_c - fill_price) / risk
        trade_status = "STILL_OPEN"
        consolidated_rr = unrealized
    elif not leg2_done:
        last_c = future_bars["close"].iloc[-1]
        unrealized_leg2 = sign * (last_c - fill_price) / risk
        trade_status = "PARTIAL_TP1_RUNNER_OPEN"
        consolidated_rr = 0.5 * 2.0 + 0.5 * unrealized_leg2
    else:
        trade_status = "CLOSED"
        consolidated_rr = 0.5 * leg1_rr + 0.5 * leg2_rr
        
    print(f"\n[{tag}] Event: {ev_uuid}")
    print(f"  Signal Time: {sig_time} | Sym: {sym} | Dir: {direction} | Fill: {fill_price} at {fill_time} | SL: {sl} | Risk: {risk:.4f}")
    print(f"  Replay Status: {trade_status} | Leg1: {leg1_exit_reason} (RR={leg1_rr}) | Leg2: {leg2_exit_reason} (RR={leg2_rr}) | Net RR: {consolidated_rr:+.2f}R")
    print(f"  Broker Trade Proxy: Outcome={ev['market_outcome']} | RR={ev['market_rr']:+.2f}R")
    print(f"  Variants: {ev['variants']}")
