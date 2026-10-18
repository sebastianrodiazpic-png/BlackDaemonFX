import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import sqlite3
import json
import pandas as pd
import numpy as np
from datetime import datetime, timezone
from marketdata.deriv import DerivMarketDataProvider

# Fetch signals from trading_bot.sqlite3
live_db = Path.home() / "AppData/Local/BlackDaemonFx/trading_bot.sqlite3"
conn = sqlite3.connect(f"file:{live_db.resolve()}?mode=ro", uri=True)
cur = conn.cursor()

ids = [21234, 21237, 21252, 21255, 21257, 21260, 21268, 21272, 21279, 21286, 21290, 21299, 21302]
cur.execute(f"""
    SELECT id, instrument, timeframe, signal_time, direction, valid, created_at, details_json
    FROM signals
    WHERE id IN ({','.join(map(str, ids))})
    ORDER BY id ASC
""")
rows = cur.fetchall()
conn.close()

provider = DerivMarketDataProvider()
symbols = list(set(r[1] for r in rows))
cache_m1 = {}
print(f"Fetching M1 bars for {symbols}...")
for s in symbols:
    df = provider.get_candles(s, timeframe="M1", count=1000)
    cache_m1[s] = df

cutoff_dt = pd.to_datetime("2026-10-15T17:35:16.304722+00:00", utc=True)

def simulate_trade_forward(df_bars, start_time, direction, entry, sl, tp1, tp2):
    """Simulates trade forward bar by bar."""
    future = df_bars[df_bars["time"] >= start_time].copy().reset_index(drop=True)
    if future.empty:
        return "NO_FUTURE_DATA", 0.0, None, None, 0
    
    sign = 1 if direction == "BUY" else -1
    risk = abs(entry - sl)
    if risk <= 0:
        return "INVALID_RISK", 0.0, None, None, 0
        
    leg1_done = False
    leg1_rr = 0.0
    leg1_time = None
    
    leg2_done = False
    leg2_rr = 0.0
    leg2_time = None
    
    active_sl_leg2 = sl
    bars_held = 0
    
    for idx, b in future.iterrows():
        bars_held = idx + 1
        t = b["time"]
        high = b["high"]
        low = b["low"]
        
        # Check Leg 1
        if not leg1_done:
            hit_sl = low <= sl if direction == "BUY" else high >= sl
            hit_tp1 = high >= tp1 if direction == "BUY" else low <= tp1
            
            if hit_sl and hit_tp1:
                # Conservative rule: SL wins on same bar
                leg1_done = True
                leg1_rr = -1.0
                leg1_time = t
                leg2_done = True
                leg2_rr = -1.0
                leg2_time = t
                return "SL_SAME_BAR_CONFLICT", -1.0, t, t, bars_held
            elif hit_sl:
                leg1_done = True
                leg1_rr = -1.0
                leg1_time = t
                leg2_done = True
                leg2_rr = -1.0
                leg2_time = t
                return "SL_LOSS", -1.0, t, t, bars_held
            elif hit_tp1:
                leg1_done = True
                leg1_rr = 2.0
                leg1_time = t
                active_sl_leg2 = entry # move to Breakeven
                
        # Check Leg 2 if Leg 1 hit TP1
        if leg1_done and not leg2_done:
            hit_be = low <= active_sl_leg2 if direction == "BUY" else high >= active_sl_leg2
            hit_tp2 = high >= tp2 if direction == "BUY" else low <= tp2
            
            if hit_be and hit_tp2:
                leg2_done = True
                leg2_rr = 0.0
                leg2_time = t
                # Consolidated: 50% TP1 (2R) + 50% BE (0R) = +1.0R
                return "TP1_WIN_RUNNER_BE_SAME_BAR", 1.0, leg1_time, t, bars_held
            elif hit_be:
                leg2_done = True
                leg2_rr = 0.0
                leg2_time = t
                return "TP1_WIN_RUNNER_BE", 1.0, leg1_time, t, bars_held
            elif hit_tp2:
                leg2_done = True
                leg2_rr = 4.0
                leg2_time = t
                # Consolidated: 50% TP1 (2R) + 50% TP2 (4R) = +3.0R
                return "FULL_TP2_WIN", 3.0, leg1_time, t, bars_held
                
    # If still open after all available bars
    last_c = future["close"].iloc[-1]
    if not leg1_done:
        unrealized = sign * (last_c - entry) / risk
        return "STILL_OPEN", unrealized, None, None, bars_held
    else:
        unrealized_leg2 = sign * (last_c - entry) / risk
        cons = 0.5 * 2.0 + 0.5 * unrealized_leg2
        return "TP1_WIN_RUNNER_OPEN", cons, leg1_time, None, bars_held

print("\n" + "="*115)
print("REPLAY INDEPENDIENTE M1 CON ENTRADA EXACTA EN CREATED_AT (SIN LOOKAHEAD / ZERO AMBIGUITY)")
print("="*115)

for r in rows:
    src_id = r[0]
    sym = r[1]
    tf = r[2]
    sig_time_str = r[3]
    direction = r[4]
    created_at_str = r[6]
    det = json.loads(r[7]) if r[7] else {}
    strategy = "MSNR" if "setup_type" in det or "msnr" in str(det).lower() else "ICT"
    
    sig_time = pd.to_datetime(sig_time_str, utc=True)
    created_at = pd.to_datetime(created_at_str, utc=True)
    is_prospect = sig_time >= cutoff_dt
    tag = "PROSPECTIVE" if is_prospect else "PRE_CUTOFF"
    
    entry = float(det.get("entry_price"))
    sl = float(det.get("stop_loss"))
    risk = abs(entry - sl)
    sign = 1 if direction == "BUY" else -1
    
    # 2R TP1, 4R TP2
    tp1 = entry + sign * 2.0 * risk
    tp2 = entry + sign * 4.0 * risk
    
    df_bars = cache_m1.get(sym)
    
    # Run simulation forward starting from created_at (when signal became available to execute)
    outcome, rr, t1, t2, bars = simulate_trade_forward(df_bars, created_at, direction, entry, sl, tp1, tp2)
    
    # Also get first bar after created_at
    future_after = df_bars[df_bars["time"] >= created_at]
    first_bar_time = future_after["time"].iloc[0] if not future_after.empty else "N/A"
    first_open = future_after["open"].iloc[0] if not future_after.empty else 0.0
    
    print(f"[{tag}] ID {src_id} | Strat: {strategy} | {sym} {direction}")
    print(f"   SigTime: {sig_time} | CreatedAt: {created_at} | 1st Bar: {first_bar_time} (Open: {first_open})")
    print(f"   Entry: {entry} | SL: {sl} | TP1: {tp1:.2f} | Risk: {risk:.4f}")
    print(f"   Result: Outcome={outcome:<25} | Cons RR={rr:+.2f}R | Bars Held={bars} | TP1 Time={t1} | Exit Time={t2}")
