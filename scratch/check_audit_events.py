import sqlite3

conn = sqlite3.connect('file:C:/Users/sebas/AppData/Local/BlackDaemonFx/trading_bot.sqlite3?mode=ro', uri=True)
conn.row_factory = sqlite3.Row
c = conn.cursor()

print('\nRecent warning/error/failed events (Last 15):')
c.execute("SELECT id, created_at, event_type, instrument, action, reason FROM daemon_audit_events WHERE event_type LIKE '%ERR%' OR event_type LIKE '%WARN%' OR event_type LIKE '%FAIL%' OR reason LIKE '%error%' ORDER BY id DESC LIMIT 15")
rows = c.fetchall()
if not rows:
    print("  None found! Zero error/fail events in audit log.")
for r in rows:
    d = dict(r)
    print(f"  #{d.get('id')} [{d.get('created_at')}] {d.get('event_type')} | Instrument: {d.get('instrument')} | Action: {d.get('action')} | Reason: {d.get('reason')}")

# Check all active workers and their current cycle
print('\nActive Worker Status Breakdown:')
c.execute("SELECT bot_profile, status, pid, cycle_number, symbols_total, symbols_processed, current_symbol, last_action, last_reason, updated_at FROM worker_runtime_states WHERE status != 'DISABLED_BY_CONFIG' AND status != 'SUPERSEDED' ORDER BY updated_at DESC")
for r in c.fetchall():
    d = dict(r)
    print(f"  Profile: {d.get('bot_profile'):<14} | Status: {d.get('status'):<20} | PID: {d.get('pid')} | Cycle: {d.get('cycle_number')} | Symbol: {d.get('current_symbol')} | Updated: {d.get('updated_at')}")
    if d.get('last_reason'):
        print(f"    -> Reason: {d.get('last_reason')}")

conn.close()
