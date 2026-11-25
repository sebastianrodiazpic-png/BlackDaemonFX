import sqlite3

conn = sqlite3.connect('storage/live_trading_bot.sqlite3')
cur = conn.cursor()

tickets = ['4797135661', '4796921802', '4796765886', '4796980220', '4796697303']
for t in tickets:
    print(f"\n================ SEARCHING TICKET {t} ================")
    cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
    for (tbl,) in cur.fetchall():
        cur.execute(f"PRAGMA table_info({tbl})")
        for col_info in cur.fetchall():
            c = col_info[1]
            try:
                cur.execute(f"SELECT rowid, * FROM {tbl} WHERE cast({c} as text) LIKE ?", (f"%{t}%",))
                rows = cur.fetchall()
                if rows:
                    print(f"MATCH in {tbl}.{c} ({len(rows)} rows):")
                    for row in rows[:3]:
                        print("  Row:", row[:6])
            except Exception as e:
                pass
