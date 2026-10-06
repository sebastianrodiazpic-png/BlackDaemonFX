import sqlite3
import pandas as pd

conn = sqlite3.connect('data/trading.db')
cur = conn.cursor()
cur.execute("SELECT name FROM sqlite_master WHERE type='table';")
tables = [t[0] for t in cur.fetchall()]
print("Tablas en data/trading.db:", tables)

for t in tables:
    cnt = pd.read_sql_query(f'SELECT count(*) as cnt FROM "{t}"', conn)['cnt'][0]
    df = pd.read_sql_query(f'SELECT * FROM "{t}" LIMIT 3', conn)
    print(f"\n--- Tabla '{t}' ({cnt} registros) ---")
    print("Columnas:", list(df.columns))
    if cnt > 0:
        print(df.head(2).to_dict(orient='records'))

conn.close()
