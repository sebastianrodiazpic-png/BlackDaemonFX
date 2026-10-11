import sqlite3
import json

db_path = r"C:\Users\sebas\AppData\Local\BlackDaemonFx\trading_bot.sqlite3"
conn = sqlite3.connect(db_path)
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

cursor.execute("""
    SELECT created_at, instrument, action, reason, payload_json
    FROM daemon_audit_events
    WHERE (payload_json LIKE '%MALAYSIAN_SNR%' OR action LIKE '%MALAYSIAN%')
      AND event_type = 'SYMBOL_PROCESS_RESULT'
      AND instrument IN ('Step Index 400', 'Crash 600 Index', 'Boom 1000 Index', 'Jump 25 Index', 'Volatility 50 (1s) Index')
    ORDER BY id DESC LIMIT 20
""")

for r in cursor.fetchall():
    print(f"[{r['created_at']}] {r['instrument']} -> Act: {r['action']} | Reason: {r['reason']}")
    pl_str = r['payload_json']
    if pl_str:
        try:
            pl = json.loads(pl_str)
            res = pl.get('result', {})
            print("   result keys:", list(res.keys()))
            if 'diagnostics' in res:
                print("   diagnostics:", res['diagnostics'])
            if 'meta_features' in res:
                print("   meta_features:", res['meta_features'])
            if 'scenario' in res:
                print("   scenario:", res['scenario'])
        except Exception as e:
            print("   error:", e)

conn.close()
