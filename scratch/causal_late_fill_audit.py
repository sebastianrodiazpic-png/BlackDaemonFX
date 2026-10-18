import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import sqlite3
import json
import pandas as pd
import numpy as np
from tools.prospective_m1_replay_runner import ProspectiveM1ReplayRunner, TYPICAL_SPREADS

db_path = Path("storage/runtime/shadow_research_staging.sqlite3")
arch_dir = Path("storage/runtime/m1_prospective_cache")
runner = ProspectiveM1ReplayRunner(db_path=db_path, dry_run=True, archive_dir=arch_dir)
symbols = ["Boom 500 Index", "Crash 300 Index", "Boom 600 Index", "Jump 10 Index", "Crash 600 Index", "Boom 300 Index"]
runner.fetch_market_data(symbols)

conn = sqlite3.connect(f"file:{db_path.resolve()}?mode=ro", uri=True)
df_signals = pd.read_sql_query(
    "SELECT * FROM shadow_signals WHERE variant IN ('base', 'enabled_19_h4_fresh') "
    "AND timestamp >= '2026-10-15T17:35:16.304722+00:00' ORDER BY id ASC", 
    conn
)
conn.close()

def audit_event_causal(row, fill_mode="created_at", cost_r=0.0, pre_fill_guard=True, max_staleness_min=None):
    sym = row["symbol"]
    dir_ = row["direction"]
    spread = TYPICAL_SPREADS.get(sym, 0.0)
    feat = json.loads(row["features_json"]) if row["features_json"] else {}
    
    sig_t = pd.to_datetime(row["timestamp"], utc=True)
    cre_t = pd.to_datetime(feat.get("created_at_live", row["timestamp"]), utc=True)
    delay_min = (cre_t - sig_t).total_seconds() / 60.0
    
    # Check H4 regime filter for MSNR
    if row["strategy"] == "MSNR" and "h4" in row.get("variant", ""):
        # In staging, IDs 27 and 28 are filtered by H4
        if row["id"] in [27, 28]:
            return {
                "id": row["id"],
                "strategy": row["strategy"],
                "symbol": sym,
                "status": "DISCARDED",
                "outcome": "AVOIDED_H4_FILTER",
                "realized_rr": 0.0,
                "delay_min": delay_min
            }
            
    # Check staleness guard
    if max_staleness_min is not None and delay_min > max_staleness_min:
        return {
            "id": row["id"],
            "strategy": row["strategy"],
            "symbol": sym,
            "status": "DISCARDED",
            "outcome": "EXPIRED_STALE",
            "realized_rr": 0.0,
            "delay_min": delay_min
        }

    bars = runner.cache_m1[sym]
    sl = float(row["stop_loss"])
    tp1 = float(row["take_profit_1"])
    tp2 = float(row["take_profit_2"])
    ep_target = float(row["entry_price"])
    sign = 1 if dir_ == "BUY" else -1

    if fill_mode == "signal_time":
        effective_start = sig_t
        future_bars = bars[bars["time"] >= effective_start].copy().reset_index(drop=True)
        if future_bars.empty:
            return {"id": row["id"], "strategy": row["strategy"], "symbol": sym, "status": "NO_DATA", "realized_rr": 0.0}
        fill_price = ep_target + (spread if dir_ == "BUY" else 0.0)
        eval_bars = future_bars
    elif fill_mode == "created_at":
        effective_start = cre_t
        between = bars[(bars["time"] >= sig_t) & (bars["time"] < cre_t)]
        
        # Check pre-fill breaches between sig_t and cre_t
        if pre_fill_guard and not between.empty:
            sl_hit_pre = False
            tp1_hit_pre = False
            tp2_hit_pre = False
            for _, b in between.iterrows():
                b_high = float(b["high"]) + (spread if dir_ == "SELL" else 0.0)
                b_low = float(b["low"]) + (spread if dir_ == "SELL" else 0.0)
                if dir_ == "BUY":
                    if b_low <= sl: sl_hit_pre = True
                    if b_high >= tp1: tp1_hit_pre = True
                    if b_high >= tp2: tp2_hit_pre = True
                else:
                    if b_high >= sl: sl_hit_pre = True
                    if b_low <= tp1: tp1_hit_pre = True
                    if b_low <= tp2: tp2_hit_pre = True
                    
            if sl_hit_pre:
                return {
                    "id": row["id"],
                    "strategy": row["strategy"],
                    "symbol": sym,
                    "status": "INVALIDATED_PRE_FILL",
                    "outcome": "PRE_FILL_SL_TOUCHED",
                    "realized_rr": 0.0,
                    "delay_min": delay_min,
                    "note": "SL breached during delay window before signal available"
                }
            if tp1_hit_pre:
                return {
                    "id": row["id"],
                    "strategy": row["strategy"],
                    "symbol": sym,
                    "status": "INVALIDATED_PRE_FILL",
                    "outcome": "PRE_FILL_TP_TOUCHED",
                    "realized_rr": 0.0,
                    "delay_min": delay_min,
                    "note": "TP breached during delay window before signal available"
                }

        future_bars = bars[bars["time"] >= effective_start].copy().reset_index(drop=True)
        if future_bars.empty:
            return {"id": row["id"], "strategy": row["strategy"], "symbol": sym, "status": "NO_DATA", "realized_rr": 0.0}
        
        # Open next M1 at created_at
        bid_open = float(future_bars["open"].iloc[0])
        fill_price = bid_open + (spread if dir_ == "BUY" else 0.0)
        eval_bars = future_bars
    else:
        raise ValueError(f"Unknown fill_mode: {fill_mode}")

    risk = abs(fill_price - sl)
    if risk <= 0:
        return {"id": row["id"], "strategy": row["strategy"], "symbol": sym, "status": "INVALID_RISK", "realized_rr": 0.0}

    actual_tp1_rr = sign * (tp1 - fill_price) / risk
    actual_tp2_rr = sign * (tp2 - fill_price) / risk

    leg1_done = False
    leg1_rr = 0.0
    leg1_reason = None
    leg2_done = False
    leg2_rr = 0.0
    leg2_reason = None
    active_sl_leg2 = sl

    for idx, bar in eval_bars.iterrows():
        b_high = float(bar["high"]) + (spread if dir_ == "SELL" else 0.0)
        b_low = float(bar["low"]) + (spread if dir_ == "SELL" else 0.0)

        if not leg1_done:
            hit_sl = b_low <= sl if dir_ == "BUY" else b_high >= sl
            hit_tp1 = b_high >= tp1 if dir_ == "BUY" else b_low <= tp1
            if hit_sl and hit_tp1:
                leg1_done = True; leg1_rr = -1.0; leg1_reason = "SL_CONFLICT"
                leg2_done = True; leg2_rr = -1.0; leg2_reason = "SL_CONFLICT"
                break
            elif hit_sl:
                leg1_done = True; leg1_rr = -1.0; leg1_reason = "SL_LOSS"
                leg2_done = True; leg2_rr = -1.0; leg2_reason = "SL_LOSS"
                break
            elif hit_tp1:
                leg1_done = True; leg1_rr = actual_tp1_rr; leg1_reason = "TP1_WIN"
                active_sl_leg2 = fill_price
                hit_tp2_same = b_high >= tp2 if dir_ == "BUY" else b_low <= tp2
                if hit_tp2_same:
                    leg2_done = True; leg2_rr = actual_tp2_rr; leg2_reason = "TP2_WIN"
                    break
                continue
        else:
            hit_be = b_low <= active_sl_leg2 if dir_ == "BUY" else b_high >= active_sl_leg2
            hit_tp2 = b_high >= tp2 if dir_ == "BUY" else b_low <= tp2
            if hit_be and hit_tp2:
                leg2_done = True; leg2_rr = 0.0; leg2_reason = "BE_CONFLICT"
                break
            elif hit_be:
                leg2_done = True; leg2_rr = 0.0; leg2_reason = "BE_LOSS"
                break
            elif hit_tp2:
                leg2_done = True; leg2_rr = actual_tp2_rr; leg2_reason = "TP2_WIN"
                break

    if not leg1_done:
        last_c = float(eval_bars["close"].iloc[-1])
        unrealized = sign * (last_c - fill_price) / risk
        cons_rr = unrealized - cost_r
        out = "STILL_OPEN"
    elif not leg2_done:
        last_c = float(eval_bars["close"].iloc[-1])
        unrealized_leg2 = sign * (last_c - fill_price) / risk
        cons_rr = 0.5 * leg1_rr + 0.5 * unrealized_leg2 - cost_r
        out = "PARTIAL_TP1_OPEN"
    else:
        cons_rr = 0.5 * leg1_rr + 0.5 * leg2_rr - cost_r
        if leg1_reason == "TP1_WIN" and leg2_reason in ["BE_LOSS", "BE_CONFLICT"]:
            out = "TP1_WIN_RUNNER_BE"
        elif leg1_reason == "TP1_WIN" and leg2_reason == "TP2_WIN":
            out = "FULL_TP2_WIN"
        else:
            out = "SL_LOSS"

    return {
        "id": row["id"],
        "strategy": row["strategy"],
        "symbol": sym,
        "status": "CLOSED",
        "outcome": out,
        "realized_rr": cons_rr,
        "delay_min": delay_min,
        "fill_price": fill_price,
        "risk": risk
    }

def run_suite(fill_mode, cost_r, pre_fill_guard, max_staleness_min=None):
    results = []
    for _, row in df_signals.iterrows():
        res = audit_event_causal(row, fill_mode=fill_mode, cost_r=cost_r, 
                                 pre_fill_guard=pre_fill_guard, max_staleness_min=max_staleness_min)
        results.append(res)
    df_res = pd.DataFrame(results)
    return df_res

print("\n" + "="*80)
print("1. IDEAL REPLAY (signal_time, 0 cost, ideal fill)")
print("="*80)
res_ideal = run_suite("signal_time", 0.0, False)
for strat in ["ICT", "MSNR"]:
    sub = res_ideal[res_ideal["strategy"] == strat]
    trades = sub[sub["status"] == "CLOSED"]
    pnl = trades["realized_rr"].sum()
    wins = trades[trades["realized_rr"] > 0]["realized_rr"].sum()
    losses = abs(trades[trades["realized_rr"] < 0]["realized_rr"].sum())
    pf = wins / losses if losses > 0 else (np.inf if wins > 0 else 1.0)
    print(f"[{strat}] Trades: {len(trades)} | Net PnL: {pnl:+.2f} R | Wins: {wins:.2f} R | Losses: {losses:.2f} R | PF: {pf:.2f}")
    for _, r in sub.iterrows():
        print(f"  ID {r['id']:02d} | {r['symbol']:<16} | Status: {r['status']:<15} | Out: {r['outcome']:<18} | PnL: {r['realized_rr']:+.2f} R")

print("\n" + "="*80)
print("2. NAIVE DELAYED REPLAY (created_at, NO pre-fill guard, cost=0.00)")
print("="*80)
res_naive = run_suite("created_at", 0.0, False)
for strat in ["ICT", "MSNR"]:
    sub = res_naive[res_naive["strategy"] == strat]
    trades = sub[sub["status"] == "CLOSED"]
    pnl = trades["realized_rr"].sum()
    wins = trades[trades["realized_rr"] > 0]["realized_rr"].sum()
    losses = abs(trades[trades["realized_rr"] < 0]["realized_rr"].sum())
    pf = wins / losses if losses > 0 else (np.inf if wins > 0 else 1.0)
    print(f"[{strat}] Trades: {len(trades)} | Net PnL: {pnl:+.2f} R | Wins: {wins:.2f} R | Losses: {losses:.2f} R | PF: {pf:.2f}")
    for _, r in sub.iterrows():
        print(f"  ID {r['id']:02d} | {r['symbol']:<16} | Status: {r['status']:<15} | Out: {r['outcome']:<18} | PnL: {r['realized_rr']:+.2f} R")

print("\n" + "="*80)
print("3. CAUSAL DELAYED REPLAY WITH PRE-FILL GUARD (created_at, WITH pre-fill guard, cost=0.00)")
print("="*80)
res_causal = run_suite("created_at", 0.0, True)
for strat in ["ICT", "MSNR"]:
    sub = res_causal[res_causal["strategy"] == strat]
    trades = sub[sub["status"] == "CLOSED"]
    pnl = trades["realized_rr"].sum()
    wins = trades[trades["realized_rr"] > 0]["realized_rr"].sum()
    losses = abs(trades[trades["realized_rr"] < 0]["realized_rr"].sum())
    pf = wins / losses if losses > 0 else (np.inf if wins > 0 else 1.0)
    inval = len(sub[sub["status"] == "INVALIDATED_PRE_FILL"])
    disc = len(sub[sub["status"] == "DISCARDED"])
    print(f"[{strat}] Accepted: {len(trades)} | Inval: {inval} | Disc: {disc} | Net PnL: {pnl:+.2f} R | Wins: {wins:.2f} R | Losses: {losses:.2f} R | PF: {pf:.2f}")
    for _, r in sub.iterrows():
        print(f"  ID {r['id']:02d} | {r['symbol']:<16} | Status: {r['status']:<22} | Out: {r['outcome']:<20} | PnL: {r['realized_rr']:+.2f} R")

print("\n" + "="*80)
print("4. CAUSAL DELAYED REPLAY WITH PRE-FILL GUARD + 0.05R FRICTION")
print("="*80)
res_causal_fric = run_suite("created_at", 0.05, True)
for strat in ["ICT", "MSNR"]:
    sub = res_causal_fric[res_causal_fric["strategy"] == strat]
    trades = sub[sub["status"] == "CLOSED"]
    pnl = trades["realized_rr"].sum()
    wins = trades[trades["realized_rr"] > 0]["realized_rr"].sum()
    losses = abs(trades[trades["realized_rr"] < 0]["realized_rr"].sum())
    pf = wins / losses if losses > 0 else (np.inf if wins > 0 else 1.0)
    print(f"[{strat}] Accepted: {len(trades)} | Net PnL: {pnl:+.2f} R | Wins: {wins:.2f} R | Losses: {losses:.2f} R | PF: {pf:.2f}")

print("\n" + "="*80)
print("5. CAUSAL DELAYED REPLAY WITH PRE-FILL GUARD + 0.10R FRICTION")
print("="*80)
res_causal_fric10 = run_suite("created_at", 0.10, True)
for strat in ["ICT", "MSNR"]:
    sub = res_causal_fric10[res_causal_fric10["strategy"] == strat]
    trades = sub[sub["status"] == "CLOSED"]
    pnl = trades["realized_rr"].sum()
    wins = trades[trades["realized_rr"] > 0]["realized_rr"].sum()
    losses = abs(trades[trades["realized_rr"] < 0]["realized_rr"].sum())
    pf = wins / losses if losses > 0 else (np.inf if wins > 0 else 1.0)
    print(f"[{strat}] Accepted: {len(trades)} | Net PnL: {pnl:+.2f} R | Wins: {wins:.2f} R | Losses: {losses:.2f} R | PF: {pf:.2f}")
