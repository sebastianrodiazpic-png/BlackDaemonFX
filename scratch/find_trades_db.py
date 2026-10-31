import glob
import sqlite3
import os

candidates = (
    glob.glob('**/*.sqlite3', recursive=True) +
    glob.glob('**/*.db', recursive=True) +
    glob.glob(os.path.expanduser('~') + '/**/*.sqlite3', recursive=True)
)

for p in set(candidates):
    try:
        conn = sqlite3.connect(p)
        tables = [t[0] for t in conn.cursor().execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()]
        if 'trades' in tables:
            cnt = conn.cursor().execute('SELECT count(*) FROM trades').fetchone()[0]
            print(f"FOUND: {p} -> {cnt} trades")
    except Exception as e:
        pass
