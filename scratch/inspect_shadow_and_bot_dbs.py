import sqlite3
import pandas as pd

# 1. shadow_research.sqlite3
uri_shadow = 'file:storage/runtime/shadow_research.sqlite3?mode=ro'
conn_s = sqlite3.connect(uri_shadow, uri=True)
df_s = pd.read_sql_query("SELECT id, timestamp, strategy, variant, symbol, direction, final_action, simulated_outcome, simulated_rr FROM shadow_signals", conn_s)
print("=== SHADOW_RESEARCH.SQLITE3 ===")
print("Total rows:", len(df_s))
print("Final action value counts:\n", df_s['final_action'].value_counts())
accepted = df_s[df_s['final_action'] == 'ACCEPT']
print("Accepted count:", len(accepted))
if len(accepted) > 0:
    print(accepted[['id', 'timestamp', 'strategy', 'symbol', 'direction', 'simulated_outcome', 'simulated_rr']])

# 2. Check trading_bot.sqlite3
try:
    uri_bot = 'file:trading_bot.sqlite3?mode=ro'
    conn_b = sqlite3.connect(uri_bot, uri=True)
    cur_b = conn_b.cursor()
    tables_b = [r[0] for r in cur_b.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()]
    print("\n=== TRADING_BOT.SQLITE3 ===")
    print("Tables:", tables_b)
    for t in tables_b:
        count = cur_b.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
        print(f"  {t}: {count} rows")
        if 'trade' in t.lower() or 'order' in t.lower() or 'exec' in t.lower():
            df_t = pd.read_sql_query(f"SELECT * FROM {t} LIMIT 5", conn_b)
            print(f"    sample columns: {df_t.columns.tolist()}")
except Exception as e:
    print("Error reading trading_bot.sqlite3:", e)
