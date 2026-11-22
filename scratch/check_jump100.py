import sqlite3
import glob

print("Checking databases...")
for db in glob.glob("storage/*.sqlite3*"):
    if "shm" in db or "wal" in db: continue
    print("---", db, "---")
    try:
        conn = sqlite3.connect(db)
        cur = conn.cursor()
        cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [r[0] for r in cur.fetchall()]
        print("Tables:", tables)
        for t in ["instruments", "active_instruments", "asset_universe", "trades", "trade_journal", "signals", "quarantined_instruments", "rejections", "evaluations"]:
            if t in tables:
                cur.execute(f"SELECT count(*) FROM {t}")
                cnt = cur.fetchone()[0]
                print(f"  {t}: total rows = {cnt}")
                # check Jump
                try:
                    cur.execute(f"SELECT * FROM {t} WHERE symbol LIKE '%Jump%' LIMIT 5")
                    rows = cur.fetchall()
                    if rows:
                        print(f"    Sample {t} Jump rows: {len(rows)}")
                        for r in rows:
                            print(f"      {r}")
                except Exception as ex:
                    pass
        conn.close()
    except Exception as e:
        print("Error:", e)
