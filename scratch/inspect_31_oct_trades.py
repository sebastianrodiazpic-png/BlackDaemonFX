import sqlite3
import pandas as pd
from datetime import datetime

for db_path in ['storage/database.sqlite', r'C:\Users\sebas\AppData\Local\BlackDaemonFx\trading_bot.sqlite3']:
    print(f"=== DB: {db_path} ===")
    try:
        conn = sqlite3.connect(db_path)
        cur = conn.cursor()
        cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [t[0] for t in cur.fetchall()]
        print("Tables:", tables)
        
        # Check trades
        if 'trades' in tables:
            df = pd.read_sql_query("SELECT * FROM trades WHERE created_at LIKE '2026-10-31%' OR updated_at LIKE '2026-10-31%' OR exit_time LIKE '2026-10-31%'", conn)
            print(f"Trades count on 2026-10-31: {len(df)}")
            if not df.empty:
                print("Columns:", df.columns.tolist())
                cols_to_show = [c for c in ['id', 'ticket', 'symbol', 'strategy', 'bot_profile', 'direction', 'action', 'pnl', 'net_profit', 'r_multiple', 'outcome', 'status', 'created_at', 'exit_time', 'close_reason'] if c in df.columns]
                print(df[cols_to_show].head(30))
                if 'pnl' in df.columns:
                    print("Total PnL:", df['pnl'].sum())
                if 'net_profit' in df.columns:
                    print("Total Net Profit:", df['net_profit'].sum())
        
        # Also check all trades if 31/10 was empty (maybe dates are slightly different or UTC vs local)
        df_recent = pd.read_sql_query("SELECT * FROM trades ORDER BY id DESC LIMIT 40", conn)
        print(f"Most recent 40 trades:")
        if not df_recent.empty:
            cols_to_show = [c for c in ['id', 'ticket', 'symbol', 'strategy', 'bot_profile', 'direction', 'action', 'pnl', 'net_profit', 'r_multiple', 'outcome', 'status', 'created_at', 'exit_time', 'close_reason'] if c in df_recent.columns]
            print(df_recent[cols_to_show].head(25))
            
        conn.close()
    except Exception as e:
        print("Error reading db:", e)
    print("\n")
