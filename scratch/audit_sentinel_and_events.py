import sqlite3
import json
from datetime import datetime

DB_PATH = r'C:\Users\sebas\AppData\Local\BlackDaemonFx\trading_bot.sqlite3'

def inspect_db():
    conn = sqlite3.connect(DB_PATH)
    
    print("=== TABLAS EN BASE DE DATOS LIVE ===")
    tables = [r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()]
    print(tables)
    
    print("\n=== ÚLTIMOS EVENTOS DE AUDITORÍA (ÚLTIMOS 25) ===")
    events = conn.execute("SELECT id, event_type, action, created_at, payload_json FROM daemon_audit_events ORDER BY id DESC LIMIT 25").fetchall()
    for e in events:
        eid, etype, action, dt, payload_raw = e
        summary = ""
        try:
            p = json.loads(payload_raw) if payload_raw else {}
            if "reason" in p:
                summary = f"reason={p.get('reason')}"
            elif "symbol" in p:
                summary = f"symbol={p.get('symbol')}, action={p.get('action')}"
            elif "symbols_count" in p:
                summary = f"symbols={p.get('symbols_count')}, worker={p.get('worker') or p.get('bot_profile')}"
        except Exception:
            summary = str(payload_raw)[:60]
        print(f"[{dt}] ID={eid} | Type={etype} | Action={action} | {summary}")

    print("\n=== EVENTOS RELACIONADOS CON CENTINELA O REGIME ===")
    regime_events = conn.execute("SELECT id, event_type, action, created_at, payload_json FROM daemon_audit_events WHERE event_type LIKE '%REGIME%' OR event_type LIKE '%SENTINEL%' OR action LIKE '%REGIME%' OR action LIKE '%CENTINELA%' ORDER BY id DESC LIMIT 10").fetchall()
    for r in regime_events:
        print(r[:4], str(r[4])[:100])

    print("\n=== ÚLTIMAS SEÑALES O CANDIDATOS EVALUADOS ===")
    if 'signals' in tables:
        sig_rows = conn.execute("SELECT id, symbol, direction, created_at, raw_signal_json FROM signals ORDER BY id DESC LIMIT 10").fetchall()
        for s in sig_rows:
            print(f"Signal id={s[0]}, sym={s[1]}, dir={s[2]}, dt={s[3]}")
    elif 'daemon_audit_events' in tables:
        sig_events = conn.execute("SELECT id, event_type, action, created_at, payload_json FROM daemon_audit_events WHERE event_type LIKE '%SIGNAL%' OR event_type LIKE '%OPPORTUNITY%' OR action LIKE '%SIGNAL%' ORDER BY id DESC LIMIT 10").fetchall()
        for se in sig_events:
            print(f"Event id={se[0]}, type={se[1]}, action={se[2]}, dt={se[3]}")

    print("\n=== ÚLTIMAS OPERACIONES (TRADES) EN CUALQUIER ESTADO ===")
    trades = conn.execute("SELECT id, instrument, bot_profile, status, entry_price, sl_price, tp1_price, opened_at FROM trades ORDER BY id DESC LIMIT 10").fetchall()
    for t in trades:
        print(t)

    conn.close()

if __name__ == '__main__':
    inspect_db()
