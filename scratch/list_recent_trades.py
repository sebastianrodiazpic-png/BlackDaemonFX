import sqlite3

db_path = r"C:\Users\sebas\AppData\Local\BlackDaemonFx\trading_bot.sqlite3"
conn = sqlite3.connect(db_path)
conn.row_factory = sqlite3.Row
cur = conn.cursor()

rows = cur.execute("""
    SELECT id, broker_position_ticket, instrument, direction, volume, net_pnl, 
           planned_rr, realized_rr, exit_reason, strategy_version, setup_reason, 
           entry_time, exit_time 
    FROM trades 
    WHERE id >= 880 
    ORDER BY id ASC
""").fetchall()

print(f"Total trades >= 880: {len(rows)}")
for r in rows:
    exit_r = str(r['exit_reason'] or 'OPEN')
    rr_str = f"{r['realized_rr']:.2f}" if r['realized_rr'] is not None else "N/A"
    pnl_str = f"{r['net_pnl']:.2f}" if r['net_pnl'] is not None else "N/A"
    print(f"ID {r['id']:3d} | Ticket {r['broker_position_ticket']} | {r['instrument']:22s} | {r['direction']:4s} | Vol: {r['volume']:4.2f} | PnL: ${pnl_str:>6s} | RR: {rr_str:>5s} | Exit: {exit_r:10s} | Strat: {r['strategy_version']}")

