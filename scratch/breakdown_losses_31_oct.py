import sqlite3
import json

db_path = r'C:\Users\sebas\AppData\Local\BlackDaemonFx\trading_bot.sqlite3'
conn = sqlite3.connect(db_path)

cur = conn.cursor()
cur.execute("""
SELECT id, instrument, direction, created_at, exit_time, net_pnl, realized_rr, setup_reason, details_json 
FROM trades 
WHERE created_at LIKE '2026-10-31%' OR exit_time LIKE '2026-10-31%'
ORDER BY id ASC
""")

rows = cur.fetchall()

print(f"{'ID':<5} | {'Instrument':<22} | {'Dir':<4} | {'PnL ($)':<8} | {'RR':<7} | {'ML':<5} | {'Exp':<7} | {'Setup'}")
print("-" * 90)

losses_by_cause = {
    "negative_ml_expectation": [],
    "choppy_pullback": [],
    "counter_trend_spikes": [],
    "other": []
}

for r in rows:
    t_id, inst, direction, created_at, exit_time, net_pnl, r_rr, setup_reason, details_json = r
    d = json.loads(details_json or '{}')
    meta = d.get('metalabel') or {}
    ml_prob = meta.get('probability')
    ml_exp = meta.get('expected_return_r')
    strat = d.get('strategy') or d.get('source') or d.get('worker') or setup_reason or ''
    
    ml_prob_str = f"{ml_prob:.2f}" if ml_prob is not None else "N/A"
    ml_exp_str = f"{ml_exp:.2f}R" if ml_exp is not None else "N/A"
    pnl_str = f"{net_pnl:.2f}" if net_pnl is not None else "0.00"
    rr_str = f"{r_rr:.2f}R" if r_rr is not None else "N/A"
    
    print(f"{t_id:<5} | {inst:<22} | {direction:<4} | {pnl_str:<8} | {rr_str:<7} | {ml_prob_str:<5} | {ml_exp_str:<7} | {strat[:35]}")
    
    if net_pnl is not None and net_pnl < 0:
        if ml_exp is not None and ml_exp < 0:
            losses_by_cause["negative_ml_expectation"].append((t_id, inst, net_pnl, r_rr, ml_exp))
        elif "BOOM" in inst.upper() and direction == "SELL":
            losses_by_cause["counter_trend_spikes"].append((t_id, inst, net_pnl, r_rr))
        elif "CRASH" in inst.upper() and direction == "BUY":
            losses_by_cause["counter_trend_spikes"].append((t_id, inst, net_pnl, r_rr))
        else:
            losses_by_cause["other"].append((t_id, inst, net_pnl, r_rr, strat))

print("\n=== CLASIFICACIÓN DE PÉRDIDAS ===")
neg_ml_pnl = sum(x[2] for x in losses_by_cause["negative_ml_expectation"])
print(f"1. Trades tomados con Expectativa ML Negativa (ML Exp < 0R): {len(losses_by_cause['negative_ml_expectation'])} trades, Pérdida: ${neg_ml_pnl:.2f}")
for x in losses_by_cause["negative_ml_expectation"]:
    print(f"   - ID {x[0]}: {x[1]} PnL: ${x[2]:.2f} ({x[3]:.2f}R, Exp: {x[4]:.2f}R)")

print(f"\n2. Trades contra-spike en Boom/Crash: {len(losses_by_cause['counter_trend_spikes'])} trades")
for x in losses_by_cause["counter_trend_spikes"]:
    print(f"   - ID {x[0]}: {x[1]} PnL: ${x[2]:.2f}")

other_pnl = sum(x[2] for x in losses_by_cause["other"])
print(f"\n3. Resto de pérdidas: {len(losses_by_cause['other'])} trades, Pérdida: ${other_pnl:.2f}")
for x in losses_by_cause["other"]:
    print(f"   - ID {x[0]}: {x[1]} PnL: ${x[2]:.2f} ({x[3]:.2f}R) | Setup: {x[4][:30]}")

conn.close()
