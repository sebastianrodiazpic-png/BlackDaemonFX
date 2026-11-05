import sqlite3
import pandas as pd

db_path = r'C:/Users/sebas/AppData/Local/BlackDaemonFx/trading_bot.sqlite3'
conn = sqlite3.connect(f'file:{db_path}?mode=ro', uri=True)

query = """
SELECT id, instrument, direction, entry_time, exit_time, entry_price, stop_loss, exit_price, net_pnl, exit_reason, setup_reason
FROM trades
WHERE instrument = 'Volatility 5 Index'
ORDER BY id DESC
LIMIT 15
"""
df = pd.read_sql_query(query, conn)
print("=== TRADES EN VOLATILITY 5 INDEX ===")
print(df.to_string())
