import sqlite3
import json

db_path = r"C:\Users\sebas\AppData\Local\BlackDaemonFx\trading_bot.sqlite3"
conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
r = conn.execute(
    "SELECT payload_json FROM daemon_audit_events WHERE action='OPERACION_RECHAZADA_POR_RIESGO' AND reason='MSNR_ENTRY_CONTEXT_CHANGED' ORDER BY event_time DESC LIMIT 1"
).fetchone()[0]

res = json.loads(r).get('result', {})
print(json.dumps(res, indent=2))
