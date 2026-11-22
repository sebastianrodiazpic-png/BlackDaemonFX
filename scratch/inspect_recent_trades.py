import sqlite3
import sys
import datetime
sys.stdout.reconfigure(encoding='utf-8')

conn = sqlite3.connect('database/trading_bot.sqlite3')
cur = conn.cursor()

print("=== TABLES IN DATABASE ===")
cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = [r[0] for r in cur.fetchall()]
print(tables)

print("\n=== RECENT TRADES (last 20) ===")
try:
    cur.execute("SELECT id, symbol, strategy, direction, status, pnl, open_time, close_time, comment FROM trades ORDER BY id DESC LIMIT 20")
    rows = cur.fetchall()
    for r in rows:
        print(r)
except Exception as e:
    print("Error querying trades:", e)

print("\n=== OPEN TRADES ===")
try:
    cur.execute("SELECT id, symbol, strategy, direction, status, open_time, pnl, comment FROM trades WHERE status = 'OPEN' OR close_time IS NULL ORDER BY id DESC")
    rows = cur.fetchall()
    print(f"Total open: {len(rows)}")
    for r in rows:
        print(r)
except Exception as e:
    print("Error querying open trades:", e)

print("\n=== RECENT CANDIDATE AUDITS / FUNNEL / OPPORTUNITIES ===")
for t in ['candidate_audit', 'msnr_candidates', 'trade_audits', 'rejected_signals', 'daily_targets']:
    if t in tables:
        print(f"\n--- Table {t} ---")
        cur.execute(f"SELECT * FROM {t} ORDER BY rowid DESC LIMIT 10")
        for r in cur.fetchall():
            print(r)
