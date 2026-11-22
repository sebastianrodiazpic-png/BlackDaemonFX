import json
import sqlite3

p = r"C:\Users\sebas\AppData\Local\BlackDaemonFx\trading_bot.sqlite3"
conn = sqlite3.connect(f"file:{p}?mode=ro", uri=True)

target_ids = [1971, 1973, 1975, 1978, 1984, 1988]

cur = conn.cursor()
for tid in target_ids:
    row = cur.execute("""
        SELECT id, instrument, direction, source, entry_time, exit_time, entry_price, stop_loss, take_profit, net_pnl, realized_rr, setup_reason, details_json
        FROM trades WHERE id = ?
    """, (tid,)).fetchone()
    if row:
        print(f"\n==================== TRADE #{row[0]}: {row[1]} ({row[2]}) ====================")
        print(f"Hora: {row[4]} -> {row[5]}")
        print(f"Precios: Entrada={row[6]}, SL={row[7]}, TP={row[8]}")
        print(f"Resultado: PNL=${row[9]}, Realized_RR={row[10]}")
        print(f"Setup Reason: {row[11]}")
        if row[12]:
            try:
                dt = json.loads(row[12])
                print("DETALLES AUDITORÍA:")
                # print human criteria if present
                if "human_criteria" in dt:
                    print("  Human Criteria:", dt["human_criteria"])
                if "ml_prediction" in dt or "ai_metadata" in dt:
                    print("  AI Metadata:", dt.get("ai_metadata") or dt.get("ml_prediction"))
                if "confluence_score" in dt:
                    print("  Confluence:", dt.get("confluence_score"))
                if "retest_evidence" in dt:
                    print("  Retest:", dt.get("retest_evidence"))
                if "scenario" in dt:
                    print("  Scenario:", dt.get("scenario"))
            except Exception as e:
                print("Error parsing json:", e)
