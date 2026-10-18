"""
scratch/check_live_trades_status.py
===================================
Inspecciona si las señales post-corte en trading_bot.sqlite3 se ejecutaron
o cerraron en el mercado real. SOLO LECTURA (?mode=ro).
"""
import sqlite3
import json
from pathlib import Path

live_db = Path.home() / "AppData/Local/BlackDaemonFx/trading_bot.sqlite3"

conn = sqlite3.connect(f"file:{live_db}?mode=ro", uri=True)
conn.row_factory = sqlite3.Row
cur = conn.cursor()

cur.execute("SELECT count(*) FROM trades WHERE entry_time >= '2026-10-15 17:35:16'")
print(f"Trades en tabla 'trades' post 17:35:16: {cur.fetchone()[0]}")

cur.execute("""
    SELECT id, instrument, direction, entry_time, exit_time, net_pnl, realized_rr, result, exit_reason
    FROM trades
    WHERE entry_time >= '2026-10-15 17:35:16'
    ORDER BY id DESC LIMIT 15
""")
rows = cur.fetchall()
for r in rows:
    print(f"  Trade ID={r['id']} | {r['instrument']} {r['direction']} | Entry: {r['entry_time']} | Exit: {r['exit_time']} | NetPnL: {r['net_pnl']} | R: {r['realized_rr']} | Res: {r['result']}")

# Check open trades (exit_time is null or status='OPEN')
cur.execute("SELECT count(*) FROM trades WHERE exit_time IS NULL")
print(f"Trades abiertos en 'trades' (exit_time is null): {cur.fetchone()[0]}")

cur.execute("""
    SELECT id, instrument, direction, entry_time, entry_price, stop_loss, take_profit
    FROM trades
    WHERE exit_time IS NULL
""")
for r in cur.fetchall():
    print(f"  Abierto: ID={r['id']} | {r['instrument']} {r['direction']} @ {r['entry_time']}")

conn.close()
