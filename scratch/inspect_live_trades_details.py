import sqlite3
import pandas as pd
from pathlib import Path

live_db = Path.home() / "AppData/Local/BlackDaemonFx/trading_bot.sqlite3"
print(f"Opening {live_db} in mode=ro")

conn = sqlite3.connect(f"file:{live_db.resolve()}?mode=ro", uri=True)
cur = conn.cursor()

cur.execute("""
    SELECT id, instrument, direction, entry_time, exit_time, entry_price, exit_price, stop_loss, take_profit, volume, realized_rr, net_pnl, exit_reason, execution_key
    FROM trades
    WHERE id IN (922, 923, 926, 927, 928, 929)
    ORDER BY id ASC
""")
trades = cur.fetchall()
cols = [d[0] for d in cur.description]
df_trades = pd.DataFrame(trades, columns=cols)
print("\n--- TRADES PRODUCTIVOS EN MT5 (LIVE_TRADE_PROXY) ---")
print(df_trades.to_string())

cur.execute("""
    SELECT id, instrument, timeframe, signal_time, direction, valid, created_at
    FROM signals
    WHERE id IN (21290, 21299, 21302)
""")
sigs = cur.fetchall()
cols_sig = [d[0] for d in cur.description]
df_sigs = pd.DataFrame(sigs, columns=cols_sig)
print("\n--- SEÑALES PRODUCTIVAS EN TRADING_BOT ---")
print(df_sigs.to_string())

conn.close()
