import sqlite3

conn = sqlite3.connect('storage/database.sqlite')
cur = conn.cursor()
cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
print('Tables in storage/database.sqlite:', [r[0] for r in cur.fetchall()])
conn.close()
