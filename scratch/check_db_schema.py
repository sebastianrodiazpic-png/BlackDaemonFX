import sqlite3

def check_db(path):
    print("=== DB:", path, "===")
    try:
        conn = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
        cur = conn.cursor()
        cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cur.fetchall()
        for t in tables:
            tname = t[0]
            cur.execute(f"PRAGMA table_info({tname})")
            cols = [c[1] for c in cur.fetchall()]
            cur.execute(f"SELECT COUNT(*) FROM {tname}")
            count = cur.fetchone()[0]
            print(f"Table: {tname} ({count} rows) -> Cols: {cols}")
        conn.close()
    except Exception as e:
        print(f"Error checking {path}: {e}")

check_db("storage/runtime/shadow_research.sqlite3")
check_db("storage/analysis/historical_analysis.db")
