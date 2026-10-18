import sqlite3
import pandas as pd

conn = sqlite3.connect('file:storage/runtime/shadow_research.sqlite3?mode=ro', uri=True)
df = pd.read_sql_query("SELECT id, timestamp, strategy, variant, symbol, direction, simulated_outcome, simulated_rr FROM shadow_signals WHERE final_action='ACCEPTED_EXECUTION'", conn)
print("Outcomes value counts:\n", df['simulated_outcome'].value_counts())
print("\nUnique outcomes:", df['simulated_outcome'].unique())

# Filter for completed/closed outcomes
closed = df[~df['simulated_outcome'].isin(['PENDING_EVALUATION', 'OPEN', None]) & df['simulated_outcome'].notna()]
print(f"\nClosed rows count: {len(closed)}")
print(closed)

print("\n=== MARKET_OUTCOME QUERY ===")
df_mkt = pd.read_sql_query("SELECT id, timestamp, strategy, variant, symbol, direction, market_outcome, market_rr FROM shadow_signals WHERE market_outcome IS NOT NULL AND market_outcome != ''", conn)
print("\n=== MSNR MARKET_OUTCOME DETAILS ===")
df_msnr_mkt = df_mkt[df_mkt['strategy'] == 'MSNR']
print(df_msnr_mkt[['id', 'timestamp', 'variant', 'symbol', 'direction', 'market_outcome', 'market_rr']])
print("MSNR closed market outcomes count:")
print(df_msnr_mkt['market_outcome'].value_counts())
