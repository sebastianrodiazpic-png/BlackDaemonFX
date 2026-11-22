import sqlite3

con = sqlite3.connect('database/trading_bot.sqlite3')
cur = con.cursor()

print("--- Tables ---")
cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = [r[0] for r in cur.fetchall()]
print(tables)

for t in tables:
    try:
        cur.execute(f"SELECT count(*) FROM {t}")
        cnt = cur.fetchone()[0]
        if cnt > 0:
            print(f"Table {t}: {cnt} rows")
    except Exception as e:
        pass

# Check recent trades in trades table
if 'trades' in tables:
    print("\n--- Recent Trades (Jump / MSNR) ---")
    cur.execute("SELECT * FROM trades ORDER BY id DESC LIMIT 10")
    cols = [d[0] for d in cur.description]
    for row in cur.fetchall():
        d = dict(zip(cols, row))
        print(f"ID={d.get('id')} sym={d.get('symbol')} strat={d.get('strategy')} magic={d.get('magic')} lot={d.get('volume', d.get('lots'))} sl={d.get('stop_loss', d.get('sl'))} tp={d.get('take_profit', d.get('tp'))} pnl={d.get('pnl')} status={d.get('status')} comment={d.get('comment')}")

# Also check any other table with 'trade' or 'order'
for t in tables:
    if any(k in t.lower() for k in ['order', 'position', 'signal', 'audit']):
        print(f"\n--- Recent rows in {t} ---")
        cur.execute(f"SELECT * FROM {t} ORDER BY rowid DESC LIMIT 5")
        cols = [d[0] for d in cur.description]
        for row in cur.fetchall():
            print(dict(zip(cols, row)))
