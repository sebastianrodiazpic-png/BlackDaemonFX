import sqlite3
import json

db_path = r"C:\Users\sebas\AppData\Local\BlackDaemonFx\trading_bot.sqlite3"
conn = sqlite3.connect(db_path)
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

# Buscar todos los eventos de auditoría emitidos por MALAYSIAN_SNR en los últimos 20 minutos
cursor.execute("""
    SELECT id, created_at, instrument, action, reason, payload_json
    FROM daemon_audit_events
    WHERE (payload_json LIKE '%MALAYSIAN_SNR%' OR action LIKE '%MALAYSIAN%')
      AND event_type = 'SYMBOL_PROCESS_RESULT'
    ORDER BY id DESC LIMIT 200
""")
rows = cursor.fetchall()

print(f"Total eventos SYMBOL_PROCESS_RESULT de Malaysian SNR encontrados: {len(rows)}")

seen_symbols = set()
by_symbol = {}
for r in rows:
    sym = r["instrument"]
    if sym not in by_symbol:
        by_symbol[sym] = {
            "created_at": r["created_at"],
            "action": r["action"],
            "reason": r["reason"],
            "payload": r["payload_json"]
        }

print(f"\n=== EVALUACION POR SIMBOLO EN MALAYSIAN SNR ({len(by_symbol)} simbolos capturados) ===")
for sym, data in sorted(by_symbol.items()):
    print(f"\n* [{sym}]")
    print(f"   Hora: {data['created_at']}")
    print(f"   Accion: {data['action']}")
    print(f"   Motivo: {data['reason']}")
    payload_str = data["payload"]
    if payload_str:
        try:
            pl = json.loads(payload_str)
            res = pl.get("result", {})
            an = res.get("analysis", {})
            adx = res.get("momentum_adx") or an.get("adx")
            scen = res.get("scenario") or an.get("scenario")
            direc = res.get("direction") or an.get("direction")
            if adx is not None:
                print(f"   ADX: {adx}")
            if scen:
                print(f"   Scenario: {scen}")
            if direc:
                print(f"   Direction: {direc}")
            diag = res.get("diagnostics") or an.get("diagnostics")
            if diag:
                print(f"   Diagnostics: {diag}")
        except Exception as exc:
            print("   Error parsing payload:", exc)

conn.close()
