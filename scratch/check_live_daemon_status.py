import sqlite3
import os
import json

db_path = 'C:/Users/sebas/AppData/Local/BlackDaemonFx/trading_bot.sqlite3'
print('Checking DB at:', db_path)
if not os.path.exists(db_path):
    print('DB does not exist at path.')
    exit(1)

conn = sqlite3.connect(f'file:{db_path}?mode=ro', uri=True)
conn.row_factory = sqlite3.Row
c = conn.cursor()

c.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = [r[0] for r in c.fetchall()]
print('Available tables:', tables)

# Check worker_runtime_states
if 'worker_runtime_states' in tables:
    print('\n=== Worker Runtime States ===')
    c.execute("SELECT * FROM worker_runtime_states ORDER BY updated_at DESC LIMIT 15")
    rows = c.fetchall()
    for r in rows:
        d = dict(r)
        print(f"Worker: {d.get('worker_id') or d.get('profile')} | Updated: {d.get('updated_at')} | State: {d.get('state')} | Cycles: {d.get('cycle_count')} | Last Error: {d.get('last_error')}")

# Check daemon_audit_events
if 'daemon_audit_events' in tables:
    print('\n=== Recent Daemon Audit Events (Last 15) ===')
    c.execute("SELECT * FROM daemon_audit_events ORDER BY id DESC LIMIT 15")
    rows = c.fetchall()
    for r in rows:
        d = dict(r)
        print(f"[{d.get('created_at') or d.get('timestamp')}] {d.get('event_type') or d.get('action')}: {d.get('message') or d.get('detail') or d.get('reason')}")

# Check account_snapshots columns
if 'account_snapshots' in tables:
    c.execute("PRAGMA table_info(account_snapshots)")
    cols = [col[1] for col in c.fetchall()]
    print(f'\n=== Account Snapshots (Cols: {cols}) ===')
    sort_col = 'created_at' if 'created_at' in cols else (cols[0])
    c.execute(f"SELECT * FROM account_snapshots ORDER BY {sort_col} DESC LIMIT 5")
    for r in c.fetchall():
        d = dict(r)
        print(f"[{d.get('created_at') or d.get('timestamp')}] Balance: {d.get('balance')}, Equity: {d.get('equity')}, Positions: {d.get('open_positions') or d.get('positions_count')}")

# Check open trades
if 'trades' in tables:
    c.execute("PRAGMA table_info(trades)")
    cols = [col[1] for col in c.fetchall()]
    print(f'\n=== Open / Recent Trades (Cols: {cols}) ===')
    sort_col = 'id' if 'id' in cols else (cols[0])
    status_filter = "WHERE status='OPEN'" if 'status' in cols else ""
    c.execute(f"SELECT * FROM trades {status_filter} ORDER BY {sort_col} DESC LIMIT 10")
    rows = c.fetchall()
    print(f"Found {len(rows)} open/recent trades:")
    for r in rows:
        d = dict(r)
        print(f"Trade #{d.get('id')}: {d.get('symbol')} {d.get('direction')} | Entry: {d.get('entry_price')} | Current/Exit: {d.get('exit_price')} | PnL: {d.get('pnl')} | Status: {d.get('status')} | Strategy: {d.get('strategy')}")

# Check signals
if 'signals' in tables:
    c.execute("PRAGMA table_info(signals)")
    cols = [col[1] for col in c.fetchall()]
    sort_col = 'id' if 'id' in cols else (cols[0])
    print(f'\n=== Recent Signals (Last 10) ===')
    c.execute(f"SELECT * FROM signals ORDER BY {sort_col} DESC LIMIT 10")
    for r in c.fetchall():
        d = dict(r)
        print(f"[{d.get('created_at') or d.get('timestamp')}] {d.get('symbol')} | {d.get('strategy')} | {d.get('action')} | Reason: {d.get('reason')}")

conn.close()
