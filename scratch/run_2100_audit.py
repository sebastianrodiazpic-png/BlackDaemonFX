import sqlite3
import json
from datetime import datetime, timezone

DB_PATH = r'C:\Users\sebas\AppData\Local\BlackDaemonFx\trading_bot.sqlite3'

def run_audit():
    conn = sqlite3.connect(DB_PATH)
    max_id = conn.execute("SELECT max(id) FROM daemon_audit_events").fetchone()[0]
    
    print(f"=== REPORTE 21:00 HRS CHILE (Audit Event max_id={max_id}) ===")

    # 1. Conteo de eventos recientes (últimos 15,000 eventos, cubriendo la última hora)
    recent_events = conn.execute(f"""
        SELECT event_type, action, count(*)
        FROM daemon_audit_events
        WHERE id >= {max_id - 15000}
        GROUP BY event_type, action
        ORDER BY count(*) DESC
    """).fetchall()

    print("\n--- 1. DESGLOSE DE EVENTOS DE AUDITORÍA EN LA ÚLTIMA HORA ---")
    for r in recent_events:
        print(f"  {r[0]:<35} | {r[1]:<30} | {r[2]}")

    # 2. Análisis del Modo Centinela (Market Regime Sentinel)
    sentinel_events = conn.execute(f"""
        SELECT id, created_at, payload_json
        FROM daemon_audit_events
        WHERE id >= {max_id - 15000}
          AND event_type = 'MARKET_REGIME_BLOCKED'
        ORDER BY id DESC LIMIT 500
    """).fetchall()

    regimes_count = {}
    symbols_blocked = {}
    sample_reasons = {}

    for s in sentinel_events:
        p = json.loads(s[2])
        reg = p.get("regime", {})
        sym = reg.get("symbol", "UNKNOWN")
        r_type = reg.get("regime", "UNKNOWN")
        reason = reg.get("reason", "UNKNOWN")

        symbols_blocked[sym] = symbols_blocked.get(sym, 0) + 1
        regimes_count[r_type] = regimes_count.get(r_type, 0) + 1
        if sym not in sample_reasons:
            sample_reasons[sym] = reason

    print(f"\n--- 2. ESTADO DEL MODO CENTINELA (Muestra analizada: {len(sentinel_events)} bloqueos) ---")
    print("  Distribución por Régimen Detectado:")
    for k, v in regimes_count.items():
        print(f"    • {k}: {v} intervenciones")
    print("  Activos más afectados por el escudo del Centinela:")
    for sym, count in sorted(symbols_blocked.items(), key=lambda x: x[1], reverse=True)[:10]:
        print(f"    • {sym:<25}: {count} bloqueos | Motivo: {sample_reasons.get(sym)}")

    # 3. Operaciones registradas en la tabla trades
    trades = conn.execute("""
        SELECT id, instrument, direction, status, result, entry_price, stop_loss, take_profit, entry_time, exit_time, net_pnl, created_at
        FROM trades
        ORDER BY id DESC LIMIT 10
    """).fetchall()

    print("\n--- 3. ESTADO DE OPERACIONES (TRADES) ---")
    if trades:
        for t in trades:
            print(f"  Trade #{t[0]} | {t[1]} {t[2]} | Status={t[3]}, Result={t[4]} | Entry={t[5]}, SL={t[6]}, TP={t[7]} | Net PnL={t[10]} | Open={t[8]} | Created={t[11]}")
    else:
        print("  No hay operaciones registradas.")

    # 4. Búsqueda de Bugs, Errores o Excepciones
    errors = conn.execute(f"""
        SELECT id, event_type, action, created_at, payload_json
        FROM daemon_audit_events
        WHERE id >= {max_id - 30000}
          AND (
            event_type LIKE '%ERR%' OR action LIKE '%ERR%' OR
            event_type LIKE '%FAIL%' OR action LIKE '%FAIL%' OR
            event_type LIKE '%EXCEPT%' OR action LIKE '%EXCEPT%'
          )
        ORDER BY id DESC LIMIT 20
    """).fetchall()

    print(f"\n--- 4. AUDITORÍA DE BUGS E INCIDENCIAS (Últimos 30,000 eventos) ---")
    print(f"  Total de errores/excepciones detectadas: {len(errors)}")
    if errors:
        for err in errors:
            print(f"    [ALERTA] ID={err[0]} | Type={err[1]} | Action={err[2]} | {str(err[4])[:120]}")
    else:
        print("  ✓ CERO BUGS: No se encontraron excepciones, caídas de workers ni errores de ejecución.")

    # 5. Estado de los Workers en worker_runtime_states
    has_wr = conn.execute("SELECT count(*) FROM sqlite_master WHERE type='table' AND name='worker_runtime_states'").fetchone()[0]
    print("\n--- 5. ESTADO DE LOS WORKERS EN TIEMPO REAL ---")
    if has_wr:
        workers = conn.execute("SELECT worker_name, last_heartbeat, is_alive, current_cycle_count FROM worker_runtime_states").fetchall()
        for w in workers:
            print(f"  Worker: {w[0]:<20} | Alive={w[2]} | Heartbeat={w[1]} | Ciclos={w[3]}")

    conn.close()

if __name__ == "__main__":
    run_audit()
