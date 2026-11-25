import sqlite3
import pandas as pd

conn = sqlite3.connect('storage/live_trading_bot.sqlite3')
df = pd.read_sql_query("""
SELECT 
    instrument, 
    source, 
    timeframe,
    count(*) as count, 
    round(avg(net_pnl), 2) as avg_pnl, 
    round(sum(net_pnl), 2) as total_pnl, 
    round(avg(case when net_pnl > 0 then 1.0 else 0.0 end)*100, 1) as wr
FROM trades 
WHERE status = 'CLOSED'
GROUP BY instrument, source 
HAVING count >= 5
ORDER BY total_pnl DESC
""", conn)
print("=== TRADES AGRUPADOS POR INSTRUMENTO Y SOURCE ===")
print(df.to_string())

df_best = pd.read_sql_query("""
SELECT id, instrument, source, timeframe, direction, setup_reason, round(net_pnl,2) as net_pnl, round(realized_rr,2) as rr, entry_time, exit_time
FROM trades
WHERE status = 'CLOSED' AND net_pnl > 0
ORDER BY net_pnl DESC LIMIT 15
""", conn)
print("\n=== TOP 15 MEJORES TRADES GANADORES ===")
print(df_best.to_string())
