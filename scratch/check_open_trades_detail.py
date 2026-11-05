import sqlite3
import json

db_path = 'C:/Users/sebas/AppData/Local/BlackDaemonFx/trading_bot.sqlite3'
conn = sqlite3.connect(f'file:{db_path}?mode=ro', uri=True)
conn.row_factory = sqlite3.Row
c = conn.cursor()

# Inspect worker_runtime_states columns and rows
c.execute("PRAGMA table_info(worker_runtime_states)")
cols = [col[1] for col in c.fetchall()]
print(f"worker_runtime_states columns: {cols}")
c.execute("SELECT * FROM worker_runtime_states ORDER BY updated_at DESC")
for r in c.fetchall():
    d = dict(r)
    print("Worker state:", {k: v for k, v in d.items() if v is not None})

# Inspect Open Trades in detail
c.execute("SELECT * FROM trades WHERE status='OPEN'")
open_trades = [dict(r) for r in c.fetchall()]
print(f"\nTotal OPEN Trades: {len(open_trades)}")
for t in open_trades:
    details = {}
    if t.get('details_json'):
        try:
            details = json.loads(t['details_json'])
        except Exception:
            pass
    print(f"ID: {t.get('id')} | Symbol: {t.get('instrument')} | Dir: {t.get('direction')} | Vol: {t.get('volume')} | Entry: {t.get('entry_price')} | SL: {t.get('stop_loss')} | TP: {t.get('take_profit')} | Strategy: {t.get('strategy_version')} | EntryTime: {t.get('entry_time')} | StrategyReason: {t.get('setup_reason')}")

# Inspect recent errors in daemon_audit_events
c.execute("SELECT * FROM daemon_audit_events WHERE event_type LIKE '%ERROR%' OR event_type LIKE '%FAIL%' OR event_type LIKE '%WARN%' OR payload LIKE '%error%' ORDER BY id DESC LIMIT 10")
errs = [dict(r) for r in c.fetchall()]
print(f"\nRecent Audit Warnings/Errors: {len(errs)}")
for e in errs:
    print(f"[{e.get('created_at')}] {e.get('event_type')}: {e.get('payload')}")

# Inspect last 20 audit events
print("\nLast 20 Audit Events:")
c.execute("SELECT id, created_at, event_type, payload FROM daemon_audit_events ORDER BY id DESC LIMIT 20")
for r in c.fetchall():
    d = dict(r)
    payload_str = str(d.get('payload'))
    if len(payload_str) > 100:
        payload_str = payload_str[:100] + '...'
    print(f"#{d.get('id')} [{d.get('created_at')}] {d.get('event_type')}: {payload_str}")

conn.close()
