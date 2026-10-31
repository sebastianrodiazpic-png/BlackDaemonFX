import sqlite3
import json

db_path = r"C:\Users\sebas\AppData\Local\BlackDaemonFx\trading_bot.sqlite3"
con = sqlite3.connect(db_path)
cur = con.cursor()

cur.execute("SELECT count(*) FROM trades")
print(f"Total trades in DB: {cur.fetchone()[0]}")

cur.execute("SELECT strategy_name, count(*) FROM trades GROUP BY strategy_name")
print("Trades by strategy:", cur.fetchall())

cur.execute("SELECT id, instrument, strategy_name, status, entry_time, close_time, pnl, exit_reason FROM trades WHERE strategy_name LIKE '%ORB%' ORDER BY id DESC LIMIT 20")
rows = cur.fetchall()
print(f"Recent ORB trades ({len(rows)}):")
for r in rows:
    print(r)

cur.execute("SELECT id, instrument, strategy_name, status, entry_time, magic, tickets FROM trades WHERE status = 'OPEN'")
open_trades = cur.fetchall()
print(f"Currently open trades ({len(open_trades)}):")
for r in open_trades:
    print(r)
