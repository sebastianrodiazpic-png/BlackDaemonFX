import sqlite3
import pandas as pd

conn = sqlite3.connect('storage/live_trading_bot.sqlite3')
df = pd.read_sql_query("""
SELECT id, instrument, direction, volume, risk_percent, risk_amount, planned_rr, realized_rr, 
       status, result, exit_reason, entry_time, exit_time
FROM trades
""", conn)

print("=== TOTAL TRADES IN DB ===")
print(len(df))

print("\n=== DISTRIBUTION OF PLANNED RR ===")
print(df['planned_rr'].round(1).value_counts(dropna=False).head(15))

print("\n=== DISTRIBUTION OF RISK PERCENT ===")
print(df['risk_percent'].round(2).value_counts(dropna=False).head(15))

print("\n=== DISTRIBUTION OF REALIZED RR (CLOSED TRADES) ===")
closed_df = df[df['status'] == 'CLOSED'].copy()
print(f"Total closed trades: {len(closed_df)}")
print(closed_df['realized_rr'].round(1).value_counts(dropna=False).head(15))

print("\n=== TRADES WITH PLANNED RR = 1.0 vs 2.0 ===")
print("Planned RR 1.0 count:", len(df[df['planned_rr'].round(1) == 1.0]))
print("Planned RR 2.0 count:", len(df[df['planned_rr'].round(1) == 2.0]))
print("Planned RR > 2.0 count:", len(df[df['planned_rr'] > 2.0]))

print("\n=== BY RESULTS FOR PLANNED RR ===")
print(pd.crosstab(closed_df['planned_rr'].round(1), closed_df['result'], margins=True))

