import sqlite3
import json

db_path = r"C:\Users\sebas\AppData\Local\BlackDaemonFx\trading_bot.sqlite3"
conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
c = conn.cursor()

q = """
SELECT event_time, instrument, action, reason, payload_json 
FROM daemon_audit_events 
WHERE action = 'OPERACION_RECHAZADA_POR_RIESGO' 
  AND reason = 'MSNR_ENTRY_CONTEXT_CHANGED'
ORDER BY event_time DESC 
LIMIT 20
"""

rows = c.execute(q).fetchall()
print(f"Encontrados {len(rows)} eventos con MSNR_ENTRY_CONTEXT_CHANGED:")
for r in rows:
    print(f"\n[{r[0]}] {r[1]} | {r[2]} | {r[3]}")
    if r[4]:
        try:
            p = json.loads(r[4])
            print("  Payload keys:", list(p.keys()))
            # print details
            for k in ('symbol', 'direction', 'market_entry_price', 'signal_entry_price', 'split_failure', 'market_signal_diagnostics', 'signal'):
                if k in p:
                    v = p[k]
                    if isinstance(v, dict):
                        print(f"  {k}:", {sk: sv for sk, sv in v.items() if sk in ('ref_level', 'invalidation_level', 'atr', 'max_entry_distance_atr', 'setup_expires_at', 'setup_execution_deadline_at', 'direction', 'entry_price', 'stop_loss')})
                    else:
                        print(f"  {k}: {v}")
        except Exception as e:
            print("  Payload error:", e)

conn.close()
