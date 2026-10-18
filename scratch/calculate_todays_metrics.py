import sqlite3
import json

conn = sqlite3.connect(r"file:C:\Users\sebas\AppData\Local\BlackDaemonFx\trading_bot.sqlite3?mode=ro", uri=True)
conn.row_factory = sqlite3.Row
cur = conn.cursor()

# Get trades from today (entry_time >= 2026-10-15 00:00:00 UTC)
trades = cur.execute("""
    SELECT id, broker_position_ticket, instrument, direction, volume, entry_price, 
           exit_price, stop_loss, take_profit, planned_rr, realized_rr, net_pnl, 
           exit_reason, strategy_version, setup_reason, details_json, entry_time, exit_time, status
    FROM trades 
    WHERE entry_time >= '2026-10-15 00:00:00'
    ORDER BY id ASC
""").fetchall()

print(f"Total trades recorded for 2026-10-15: {len(trades)}")

closed_trades = [t for t in trades if t['status'] == 'CLOSED' and t['net_pnl'] != 0.0]
zero_trades = [t for t in trades if t['net_pnl'] == 0.0]
open_trades = [t for t in trades if t['status'] != 'CLOSED']

wins = [t for t in closed_trades if t['net_pnl'] > 0]
losses = [t for t in closed_trades if t['net_pnl'] < 0]

total_pnl = sum(t['net_pnl'] for t in closed_trades)
win_pnl = sum(t['net_pnl'] for t in wins)
loss_pnl = sum(t['net_pnl'] for t in losses)

print(f"\n--- PERFORMANCE SUMMARY ---")
print(f"Closed trades: {len(closed_trades)} | Open trades: {len(open_trades)} | Scratch/Zero: {len(zero_trades)}")
print(f"Wins: {len(wins)} ({len(wins)/len(closed_trades)*100:.1f}%) | Losses: {len(losses)} ({len(losses)/len(closed_trades)*100:.1f}%)")
print(f"Total Net PnL: ${total_pnl:.2f}")
print(f"Gross Profit: ${win_pnl:.2f} | Gross Loss: ${loss_pnl:.2f} | Profit Factor: {abs(win_pnl/loss_pnl):.2f}" if loss_pnl != 0 else "PF: N/A")

# By Strategy
print(f"\n--- BREAKDOWN BY STRATEGY ---")
strats = set(t['strategy_version'] for t in trades)
for s in sorted(strats):
    st_trades = [t for t in closed_trades if t['strategy_version'] == s]
    st_wins = [t for t in st_trades if t['net_pnl'] > 0]
    st_losses = [t for t in st_trades if t['net_pnl'] < 0]
    st_pnl = sum(t['net_pnl'] for t in st_trades)
    print(f"Strategy: {s}")
    print(f"  Trades: {len(st_trades)} | Wins: {len(st_wins)} | Losses: {len(st_losses)} | PnL: ${st_pnl:.2f}")

# By Asset Category
print(f"\n--- BREAKDOWN BY ASSET CATEGORY ---")
def get_cat(inst):
    if any(k in inst for k in ['Boom', 'Crash', 'Jump', 'Step', 'Volatility', 'Flip']):
        return "Synthetics (Deriv)"
    elif any(k in inst for k in ['XAU', 'XAG']):
        return "Precious Metals"
    elif any(k in inst for k in ['SP 500', 'Wall Street', 'NAS']):
        return "Indices"
    else:
        return "Forex"

cats = {}
for t in closed_trades:
    c = get_cat(t['instrument'])
    cats.setdefault(c, []).append(t)

for c, c_trades in sorted(cats.items()):
    c_wins = [t for t in c_trades if t['net_pnl'] > 0]
    c_losses = [t for t in c_trades if t['net_pnl'] < 0]
    c_pnl = sum(t['net_pnl'] for t in c_trades)
    print(f"Category: {c}")
    print(f"  Trades: {len(c_trades)} | Wins: {len(c_wins)} | Losses: {len(c_losses)} | PnL: ${c_pnl:.2f}")
