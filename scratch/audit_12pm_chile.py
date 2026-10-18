import sqlite3
import json
import datetime
import MetaTrader5 as mt5

print("=== 12:00 PM CHILE SYNCHRONIZATION AUDIT ===")
now_utc = datetime.datetime.now(datetime.timezone.utc)
now_clt = now_utc - datetime.timedelta(hours=3)
print(f"Current UTC time: {now_utc.strftime('%Y-%m-%d %H:%M:%S UTC')}")
print(f"Current Chile time: {now_clt.strftime('%Y-%m-%d %H:%M:%S CLT')}")

# Check MT5 positions
if mt5.initialize():
    pos = mt5.positions_get()
    print(f"\nMT5 Open Positions ({len(pos) if pos else 0}):")
    if pos:
        for p in pos:
            print(f"  Ticket {p.ticket} | {p.symbol} | Type {p.type} | Vol {p.volume} | Open {p.price_open} | Curr {p.price_current} | SL {p.sl} | TP {p.tp} | Profit ${p.profit:.2f}")
    mt5.shutdown()
else:
    print("Failed to init MT5")

# Check DB trades
db_path = r"C:\Users\sebas\AppData\Local\BlackDaemonFx\trading_bot.sqlite3"
conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
conn.row_factory = sqlite3.Row
cur = conn.cursor()

trades = cur.execute("""
    SELECT id, broker_position_ticket, instrument, direction, volume, entry_price, 
           exit_price, stop_loss, take_profit, planned_rr, realized_rr, net_pnl, 
           exit_reason, strategy_version, setup_reason, entry_time, exit_time, status 
    FROM trades 
    WHERE entry_time >= '2026-10-15 00:00:00' 
    ORDER BY id ASC
""").fetchall()

print(f"\nTotal trades today: {len(trades)}")
closed = [t for t in trades if t['status'] == 'CLOSED' and t['net_pnl'] != 0.0]
zero = [t for t in trades if t['net_pnl'] == 0.0]
opened = [t for t in trades if t['status'] != 'CLOSED']
wins = [t for t in closed if t['net_pnl'] > 0]
losses = [t for t in closed if t['net_pnl'] < 0]

print(f"Closed: {len(closed)} | Open in DB: {len(opened)} | Scratch: {len(zero)}")
print(f"Wins: {len(wins)} | Losses: {len(losses)}")
tot_pnl = sum(t['net_pnl'] for t in closed)
w_pnl = sum(t['net_pnl'] for t in wins)
l_pnl = sum(t['net_pnl'] for t in losses)
print(f"Net PnL: ${tot_pnl:.2f} (Gross Profit: ${w_pnl:.2f}, Gross Loss: ${l_pnl:.2f})")

print("\nRecent 10 Trades:")
for t in trades[-10:]:
    exit_r = str(t['exit_reason'] or t['status'])
    rr_str = f"{t['realized_rr']:.2f}" if t['realized_rr'] is not None else "N/A"
    pnl_str = f"{t['net_pnl']:.2f}" if t['net_pnl'] is not None else "N/A"
    print(f"  ID {t['id']:3d} | Ticket {t['broker_position_ticket']} | {t['instrument']:20s} | {t['direction']:4s} | Vol {t['volume']:4.2f} | PnL ${pnl_str:>6s} | RR {rr_str:>5s} | Exit {exit_r:10s} | Strat {t['strategy_version']}")

print("\n--- Worker Runtime States Check ---")
workers = cur.execute("SELECT id, bot_profile, status, pid, current_symbol, last_action, updated_at FROM worker_runtime_states WHERE status != 'DISABLED' ORDER BY id ASC").fetchall()
for w in workers:
    print(f"Worker {w['id']:2d} ({w['bot_profile']:15s}): status={w['status']:20s} pid={w['pid']} updated={w['updated_at']}")
