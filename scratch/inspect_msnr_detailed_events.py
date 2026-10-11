import sqlite3
import json

db_path = r"C:\Users\sebas\AppData\Local\BlackDaemonFx\trading_bot.sqlite3"
conn = sqlite3.connect(db_path)
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

print("=== 1. AUDIT EVENTS DE MALAYSIAN_SNR (ÚLTIMAS 50) ===")
cursor.execute("""
    SELECT * FROM daemon_audit_events 
    WHERE execution_key LIKE '%MALAYSIAN%' 
       OR payload_json LIKE '%MALAYSIAN%' 
       OR action LIKE '%MALAYSIAN%'
       OR reason LIKE '%MALAYSIAN%'
       OR event_type LIKE '%MALAYSIAN%'
    ORDER BY id DESC LIMIT 50
""")
events = cursor.fetchall()
print(f"Total eventos encontrados con filtro de texto: {len(events)}")
for e in events:
    d = dict(e)
    print(f"[{d.get('created_at')}] Event: {d.get('event_type')} | Sym: {d.get('instrument')} | Act: {d.get('action')} | Reason: {d.get('reason')}")
    if d.get("payload_json"):
        print("   Payload:", str(d.get("payload_json"))[:200])

print("\n=== 2. WORKER RUNTIME STATE DE MALAYSIAN_SNR DETALLADO ===")
cursor.execute("SELECT * FROM worker_runtime_states WHERE bot_profile = 'MALAYSIAN_SNR'")
msnr_state = cursor.fetchone()
if msnr_state:
    d = dict(msnr_state)
    for k, v in d.items():
        if k == "details_json" and v:
            try:
                parsed = json.loads(v)
                print(f"  {k} (parsed):")
                for pk, pv in parsed.items():
                    print(f"     {pk}: {str(pv)[:150]}")
            except Exception:
                print(f"  {k}: {v}")
        else:
            print(f"  {k}: {v}")

print("\n=== 3. TODOS LOS EVENTOS SYMBOL_PROCESS_RESULT RECIENTES ===")
cursor.execute("""
    SELECT * FROM daemon_audit_events 
    WHERE event_type = 'SYMBOL_PROCESS_RESULT' 
    ORDER BY id DESC LIMIT 30
""")
for e in cursor.fetchall():
    d = dict(e)
    print(f"[{d.get('created_at')}] Sym: {d.get('instrument')} | Act: {d.get('action')} | Reason: {d.get('reason')} | Key: {d.get('execution_key')}")

conn.close()
