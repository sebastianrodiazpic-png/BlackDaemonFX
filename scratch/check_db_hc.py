import sqlite3
import pandas as pd

conn = sqlite3.connect('file:storage/trading_bot.sqlite3?mode=ro', uri=True)
cur = conn.cursor()
tables = [r[0] for r in cur.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()]
print('Tablas en storage/trading_bot.sqlite3:', tables)

if 'daemon_audit_events' in tables:
    df_events = pd.read_sql_query("SELECT event_type, COUNT(1) as cnt FROM daemon_audit_events GROUP BY event_type", conn)
    print('\nAudit events count:')
    print(df_events)

if 'trade_records' in tables:
    cnt = cur.execute("SELECT COUNT(1) FROM trade_records").fetchone()[0]
    print(f'\nTotal trade records: {cnt}')
