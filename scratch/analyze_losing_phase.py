import sqlite3
import json
import pandas as pd
from datetime import datetime

db_path = r'C:/Users/sebas/AppData/Local/BlackDaemonFx/trading_bot.sqlite3'
conn = sqlite3.connect(f'file:{db_path}?mode=ro', uri=True)

print("=== RECENT 50 TRADES IN TRADES TABLE ===")
query = """
SELECT id, instrument, direction, status, entry_price, stop_loss, take_profit, exit_price, pnl, exit_reason, created_at, closed_at
FROM trades
ORDER BY id DESC
LIMIT 50
"""
df_trades = pd.read_sql_query(query, conn)
print(df_trades.to_string())

print("\n=== TRADES SUMMARY BY STATUS & INSTRUMENT (LAST 100) ===")
q_summary = """
SELECT instrument, 
       count(*) as total, 
       sum(case when pnl > 0 then 1 else 0 end) as wins,
       sum(case when pnl < 0 then 1 else 0 end) as losses,
       round(sum(pnl), 2) as total_pnl,
       round(avg(pnl), 2) as avg_pnl
FROM trades
WHERE status in ('CLOSED', 'STOPPED_OUT', 'TAKE_PROFIT', 'EXIT')
GROUP BY instrument
ORDER BY total_pnl ASC
"""
try:
    df_sum = pd.read_sql_query(q_summary, conn)
    print(df_sum.to_string())
except Exception as e:
    print("Error in q_summary:", e)

print("\n=== CHECK TRADE JOURNAL (IF ANY) ===")
try:
    df_journal = pd.read_sql_query("SELECT count(*) as total FROM trade_journal", conn)
    print(df_journal.to_string())
    if df_journal.iloc[0]['total'] > 0:
        df_j_recent = pd.read_sql_query("SELECT * FROM trade_journal ORDER BY id DESC LIMIT 20", conn)
        print(df_j_recent.to_string())
except Exception as e:
    print("Error in trade_journal:", e)

print("\n=== RECENT DAEMON AUDIT EVENTS WITH HUMAN CRITERIA ===")
try:
    q_audit = """
    SELECT event_type, instrument, action, reason, payload, created_at
    FROM daemon_audit_events
    WHERE event_type LIKE '%HUMAN%' OR action LIKE '%HUMAN%' OR reason LIKE '%HUMAN%'
    ORDER BY id DESC
    LIMIT 25
    """
    df_hc = pd.read_sql_query(q_audit, conn)
    print(df_hc.to_string())
except Exception as e:
    print("Error in daemon_audit_events:", e)
