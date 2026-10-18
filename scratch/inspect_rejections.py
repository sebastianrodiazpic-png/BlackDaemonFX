import sqlite3
import json

DB_PATH = r'C:\Users\sebas\AppData\Local\BlackDaemonFx\trading_bot.sqlite3'
conn = sqlite3.connect(DB_PATH)
max_id = conn.execute('SELECT max(id) FROM daemon_audit_events').fetchone()[0]

print('=== SAMPLE META_LABEL_FILTER_REJECTED (LAST 5) ===')
for r in conn.execute(f"SELECT id, event_type, created_at, payload_json FROM daemon_audit_events WHERE event_type='META_LABEL_SIGNAL_SCORED' AND id >= {max_id - 10000} ORDER BY id DESC LIMIT 5").fetchall():
    print(f"[{r[2]}] ID={r[0]}")
    p = json.loads(r[3])
    print(f"  Symbol: {p.get('symbol')}, Prob: {p.get('meta_label', {}).get('probability')}, Threshold: {p.get('meta_label', {}).get('threshold')}, Reason: {p.get('meta_label', {}).get('reason')}")

print('\n=== SAMPLE MARKET_REGIME_BLOCKED (LAST 5) ===')
for r in conn.execute(f"SELECT id, event_type, created_at, payload_json FROM daemon_audit_events WHERE event_type='MARKET_REGIME_BLOCKED' AND id >= {max_id - 10000} ORDER BY id DESC LIMIT 5").fetchall():
    print(f"[{r[2]}] ID={r[0]}")
    p = json.loads(r[3])
    reg = p.get('regime', {})
    print(f"  Symbol: {reg.get('symbol')}, Regime: {reg.get('regime')}, Reason: {reg.get('reason')}, Mode: {reg.get('mode')}")

print('\n=== SAMPLE DAILY STRIKES BLOCKED (LAST 5) ===')
for r in conn.execute(f"SELECT id, event_type, created_at, payload_json FROM daemon_audit_events WHERE event_type='SYMBOL_DAILY_STRIKES_BLOCKED' AND id >= {max_id - 10000} ORDER BY id DESC LIMIT 5").fetchall():
    print(f"[{r[2]}] ID={r[0]}")
    p = json.loads(r[3])
    print(f"  Symbol: {p.get('symbol')}, Strikes: {p.get('strikes')}, Max: {p.get('max_strikes')}")
