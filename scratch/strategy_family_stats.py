import sqlite3
import pandas as pd

conn = sqlite3.connect('storage/live_trading_bot.sqlite3')
df = pd.read_sql_query("""
SELECT 
    CASE 
        WHEN setup_reason LIKE '%MALAYSIAN_SNR%' THEN 'MALAYSIAN_SNR'
        WHEN setup_reason LIKE '%ICT%' THEN 'ICT'
        WHEN setup_reason LIKE '%COMMODITIES%' THEN 'COMMODITIES'
        WHEN setup_reason LIKE '%ORB%' THEN 'ORB'
        ELSE 'OTHER'
    END as strategy_family,
    count(*) as count,
    round(avg(net_pnl), 2) as avg_pnl,
    round(sum(net_pnl), 2) as total_pnl,
    round(avg(case when net_pnl > 0 then 1.0 else 0.0 end)*100, 1) as wr
FROM trades
WHERE source = 'DEMO' AND status = 'CLOSED'
GROUP BY strategy_family
ORDER BY total_pnl DESC
""", conn)

print("=== RESULTADOS DEMO POR FAMILIA DE ESTRATEGIA ===")
print(df.to_string())
