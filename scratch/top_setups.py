import sqlite3
import pandas as pd

conn = sqlite3.connect('storage/live_trading_bot.sqlite3')
df = pd.read_sql_query("""
SELECT 
    setup_reason,
    count(*) as count,
    round(avg(net_pnl), 2) as avg_pnl,
    round(sum(net_pnl), 2) as total_pnl,
    round(avg(case when net_pnl > 0 then 1.0 else 0.0 end)*100, 1) as wr
FROM trades
WHERE source = 'DEMO' AND status = 'CLOSED' AND setup_reason IS NOT NULL
GROUP BY setup_reason
HAVING count >= 5
ORDER BY total_pnl DESC
LIMIT 20
""", conn)

print("=== TOP SETUPS ESPECÍFICOS EN DEMO ===")
print(df.to_string())
