import sqlite3, os

for db_path in ["database/trading_bot.sqlite3", "storage/database.sqlite", "storage/trading_bot.sqlite3"]:
    if not os.path.exists(db_path):
        continue
    print(f"\n=================== {db_path} ({os.path.getsize(db_path)} bytes) ===================")
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [r[0] for r in c.fetchall()]
    print("Tables:", tables)
    for t in tables:
        try:
            c.execute(f'SELECT COUNT(*) FROM "{t}"')
            cnt = c.fetchone()[0]
            if cnt > 0:
                print(f"  {t}: {cnt} rows")
                # print last 2 rows
                c.execute(f'SELECT * FROM "{t}" ORDER BY rowid DESC LIMIT 2')
                for row in c.fetchall():
                    d = dict(row)
                    # compact
                    sub = {k: v for k, v in d.items() if v is not None and ('time' in k or 'symbol' in k or 'instrument' in k or 'pnl' in k or 'profit' in k or 'status' in k or 'reason' in k or 'name' in k or 'ticket' in k)}
                    print(f"    sample: {sub if sub else list(d.items())[:4]}")
        except Exception as e:
            print(f"  {t} err: {e}")
    conn.close()
