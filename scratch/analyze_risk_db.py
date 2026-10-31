import sqlite3
import pandas as pd

dbs = [
    'storage/trading_bot.sqlite3',
    'database/trading_bot.sqlite3'
]

for db in dbs:
    try:
        conn = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
        cur = conn.cursor()
        cur.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = [r[0] for r in cur.fetchall()]
        print(f"=== {db} ===")
        print("Tables:", tables)
        for t in ['trades', 'positions', 'audit_records', 'trade_audits']:
            if t in tables:
                cur.execute(f"SELECT COUNT(*) FROM {t};")
                print(f"  {t} rows:", cur.fetchone()[0])
        if 'trades' in tables:
            df = pd.read_sql_query("SELECT symbol, direction, realized_rr, profit_loss, exit_reason, status, strategy_name FROM trades WHERE status='CLOSED'", conn)
            print(f"Closed trades: {len(df)}")
            if len(df) > 0:
                print("Realized RR summary:")
                print(df['realized_rr'].describe())
                print("Exit reason counts:")
                print(df['exit_reason'].value_counts().head(10))
                print("Trades with realized_rr < -0.8:", (df['realized_rr'] < -0.8).sum())
                print("Trades with realized_rr between -0.2 and 0.4:", ((df['realized_rr'] >= -0.2) & (df['realized_rr'] <= 0.4)).sum())
                print("Trades with realized_rr > 0.8:", (df['realized_rr'] > 0.8).sum())
                print("Trades with realized_rr > 1.8:", (df['realized_rr'] > 1.8).sum())
                print("PnL sum:", df['profit_loss'].sum())
        conn.close()
    except Exception as e:
        print(f"Error {db}:", e)
