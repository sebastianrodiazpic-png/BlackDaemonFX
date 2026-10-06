import sqlite3
import pandas as pd

conn = sqlite3.connect(r'C:\Users\sebas\AppData\Local\BlackDaemonFx\trading_bot.sqlite3')
cur = conn.cursor()
cur.execute("SELECT name FROM sqlite_master WHERE type='table';")
tables = [t[0] for t in cur.fetchall()]
print("Tables in persistent DB:", tables)

for t in tables:
    cnt = pd.read_sql_query(f'SELECT count(*) as cnt FROM "{t}"', conn)['cnt'][0]
    print(f"  {t}: {cnt} rows")
    if 'preference' in t:
        df = pd.read_sql_query(f'SELECT * FROM "{t}"', conn)
        print("    Content:", df.to_dict(orient='records'))

conn.close()
