import sqlite3
import os

dbs = ['storage/database.sqlite', 'storage/trading_bot.sqlite3']
localapp = os.path.expandvars(r'%LOCALAPPDATA%\BlackDaemonFx\trading_bot.sqlite3')
if os.path.exists(localapp):
    dbs.append(localapp)

for db in dbs:
    if not os.path.exists(db):
        continue
    conn = sqlite3.connect(db)
    c = conn.cursor()
    c.execute("""
        SELECT id, instrument, direction, status, strategy_name, entry_time, exit_time, net_pnl, result 
        FROM trades 
        WHERE entry_time >= '2026-11-01 00:00:00' 
        ORDER BY id DESC 
        LIMIT 30
    """)
    rows = c.fetchall()
    print(f"=== DB {db}: trades today (count={len(rows)}) ===")
    for r in rows:
        print(f"ID={r[0]} | {r[1]} | {r[2]} | {r[3]} | {r[4]} | Entry={r[5]} | Exit={r[6]} | PnL={r[7]} | Res={r[8]}")
