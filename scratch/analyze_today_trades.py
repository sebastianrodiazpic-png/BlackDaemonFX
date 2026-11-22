import json
import sqlite3
import pandas as pd

p = r"C:\Users\sebas\AppData\Local\BlackDaemonFx\trading_bot.sqlite3"
conn = sqlite3.connect(f"file:{p}?mode=ro", uri=True)

print("=" * 90)
print("ANÁLISIS COMPLETO DE OPERACIONES DE HOY: JUEVES 19/11/2026")
print("=" * 90)

# 1. Extraer todos los trades con entry_time o exit_time en 2026-11-19
q_trades = """
SELECT 
    id, broker_order_ticket, broker_position_ticket, instrument, 
    source, direction, status, result, 
    entry_time, exit_time, entry_price, exit_price, stop_loss, take_profit,
    volume, planned_rr, realized_rr, exit_reason, net_pnl, setup_reason, details_json
FROM trades
WHERE (entry_time LIKE '2026-11-19%' OR exit_time LIKE '2026-11-19%')
ORDER BY entry_time ASC
"""
df_today = pd.read_sql_query(q_trades, conn)
print(f"Total trades registrados hoy (2026-11-19): {len(df_today)}")

if len(df_today) == 0:
    # Buscar por created_at o ver últimos trades
    q_latest = """
    SELECT id, instrument, source, direction, result, entry_time, exit_time, net_pnl, realized_rr
    FROM trades
    ORDER BY id DESC LIMIT 20
    """
    print("\nÚltimos 20 trades en la base de datos:")
    print(pd.read_sql_query(q_latest, conn).to_string())
else:
    # Resumen cuantitativo
    n_total = len(df_today)
    wins = (df_today["result"] == "WIN") | (df_today["net_pnl"] > 0)
    losses = (df_today["result"] == "LOSS") | (df_today["net_pnl"] < 0)
    be = (df_today["net_pnl"] == 0) | (df_today["result"] == "BE")

    n_wins = int(wins.sum())
    n_losses = int(losses.sum())
    n_be = int(be.sum())
    tot_pnl = float(df_today["net_pnl"].sum())
    tot_r = float(df_today["realized_rr"].dropna().sum())
    win_rate = (n_wins / n_total) * 100.0 if n_total > 0 else 0.0

    print(f"\n--- RESUMEN GLOBAL DEL DÍA ---")
    print(f"Total Operaciones : {n_total}")
    print(f"Ganadoras (Wins)  : {n_wins} ({win_rate:.1f}%)")
    print(f"Perdedoras (Losses): {n_losses} ({(n_losses/n_total)*100.1:.1f}%)")
    print(f"Break Even (BE)   : {n_be}")
    print(f"PNL Neto Total    : ${tot_pnl:+.2f} USD")
    print(f"R Total Realizado : {tot_r:+.2f} R")

    # Desglose por estrategia / source
    print("\n--- DESGLOSE POR ESTRATEGIA / ORIGEN ---")
    for src, grp in df_today.groupby("source"):
        w = int(((grp["result"] == "WIN") | (grp["net_pnl"] > 0)).sum())
        l = int(((grp["result"] == "LOSS") | (grp["net_pnl"] < 0)).sum())
        pnl_s = float(grp["net_pnl"].sum())
        r_s = float(grp["realized_rr"].dropna().sum())
        wr_s = (w / len(grp)) * 100.0 if len(grp) > 0 else 0.0
        print(f"  * {src:20s}: {len(grp):2d} trades | {w}W / {l}L ({wr_s:4.1f}% WR) | PNL: ${pnl_s:+7.2f} | R: {r_s:+5.2f} R")

    # Desglose por instrumento
    print("\n--- DESGLOSE POR INSTRUMENTO ---")
    for inst, grp in df_today.groupby("instrument"):
        w = int(((grp["result"] == "WIN") | (grp["net_pnl"] > 0)).sum())
        l = int(((grp["result"] == "LOSS") | (grp["net_pnl"] < 0)).sum())
        pnl_i = float(grp["net_pnl"].sum())
        r_i = float(grp["realized_rr"].dropna().sum())
        print(f"  * {inst:28s}: {len(grp):2d} trades | {w}W / {l}L | PNL: ${pnl_i:+7.2f} | R: {r_i:+5.2f} R")

    # Detalle cronológico de cada trade
    print("\n--- DETALLE DE TODAS LAS OPERACIONES DE HOY ---")
    for idx, r in df_today.iterrows():
        pnl = float(r["net_pnl"])
        rr = float(r["realized_rr"]) if pd.notnull(r["realized_rr"]) else 0.0
        details = {}
        if r["details_json"]:
            try:
                details = json.loads(r["details_json"])
            except Exception:
                pass
        
        # Evaluar momento relativo al reinicio (~11:15 UTC / 08:15 Local)
        entry_t = str(r["entry_time"])
        restart_mark = "ANTES DEL REINICIO" if "T" in entry_t and entry_t.split("T")[1] < "11:15" or " " in entry_t and entry_t.split(" ")[1] < "11:15" else "DESPUÉS DEL REINICIO"

        print(f"\n[#{r['id']}] {r['instrument']} | {r['direction']} | {r['source']} | Result: {r['result']} ({r['exit_reason']})")
        print(f"    Hora Entrada: {r['entry_time']} ({restart_mark}) | Salida: {r['exit_time']}")
        print(f"    Precio Ent: {r['entry_price']} | SL: {r['stop_loss']} | TP: {r['take_profit']}")
        print(f"    PNL: ${pnl:+.2f} USD | Realized RR: {rr:+.2f} R | Planned RR: {r['planned_rr']}")
        print(f"    Setup Reason: {r['setup_reason']}")
        if "human_criteria" in details:
            hc = details["human_criteria"]
            print(f"    Auditoría Criterio Humano: Score={hc.get('score')} | Grade={hc.get('grade')} | Action={hc.get('action')}")
        if "retest_evidence" in details:
            re = details["retest_evidence"]
            print(f"    Retest Evidence: {re}")
        if "exit_evaluation" in details:
            print(f"    Exit Eval: {details['exit_evaluation']}")

# 2. Consultar auditorías visuales y eventos de auditoría de hoy
q_audits = """
SELECT id, event_type, instrument, action, reason, created_at, payload_json
FROM daemon_audit_events
WHERE created_at LIKE '2026-11-19%'
ORDER BY id DESC LIMIT 30
"""
try:
    df_events = pd.read_sql_query(q_audits, conn)
    print(f"\nTotal daemon_audit_events de hoy: {len(df_events)}")
    print("Muestra de eventos recientes:")
    for _, ev in df_events.head(10).iterrows():
        print(f"  {ev['created_at']} | {ev['instrument']} | {ev['event_type']} -> {ev['action']} | {ev['reason']}")
except Exception as e:
    print(f"Error consultando daemon_audit_events: {e}")
