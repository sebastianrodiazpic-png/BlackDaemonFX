import sqlite3
import json
import time
from datetime import datetime, timezone
from pathlib import Path
import pandas as pd

DB_PATH = Path(r"C:\Users\sebas\AppData\Local\BlackDaemonFx\trading_bot.sqlite3")
if not DB_PATH.exists():
    DB_PATH = Path("trading_bot.sqlite3")

print("=" * 80)
print(f"VERIFICACION DEL ESTADO EN VIVO DE WORKERS Y MODELOS GBDT")
print(f"Base de datos: {DB_PATH}")
print(f"Hora actual UTC: {datetime.now(timezone.utc).isoformat()}")
print("=" * 80)

conn = sqlite3.connect(DB_PATH)

# 1. Estados de Workers en worker_runtime_states
print("\n--- 1. ESTADO DE LOS WORKERS (worker_runtime_states) ---")
try:
    df_workers = pd.read_sql_query("""
        SELECT worker_name, status, active_symbol, last_seen, updated_at, details_json
        FROM worker_runtime_states
        ORDER BY updated_at DESC
    """, conn)
    if df_workers.empty:
        print("No hay registros en worker_runtime_states.")
    else:
        for idx, row in df_workers.iterrows():
            details = {}
            if row['details_json']:
                try:
                    details = json.loads(row['details_json'])
                except Exception:
                    pass
            last = row['updated_at'] or row['last_seen']
            print(f"• Worker: {row['worker_name']:<18} | Status: {row['status']:<10} | Simbolo: {str(row['active_symbol']):<18} | Ultima vez: {last}")
            if details:
                cycle = details.get('cycle', '')
                quote = details.get('last_quote', details.get('quote', ''))
                msg = details.get('message', details.get('status_message', ''))
                if quote or msg or cycle:
                    print(f"    Info: quote={quote} | msg={msg} | cycle={cycle}")
except Exception as exc:
    print(f"Error consultando worker_runtime_states: {exc}")

# 2. Ultimos Eventos de Auditoria (daemon_audit_events)
print("\n--- 2. ULTIMOS EVENTOS DE AUDITORIA (daemon_audit_events) ---")
try:
    df_events = pd.read_sql_query("""
        SELECT event_type, instrument, action, reason, timestamp
        FROM daemon_audit_events
        ORDER BY id DESC LIMIT 12
    """, conn)
    if df_events.empty:
        print("No hay eventos recientes en daemon_audit_events.")
    else:
        for idx, row in df_events.iterrows():
            print(f"[{row['timestamp']}] {row['event_type']:<26} | {str(row['instrument']):<16} | {str(row['action']):<18} | {str(row['reason'])[:40]}")
except Exception as exc:
    print(f"Error consultando daemon_audit_events: {exc}")

# 3. Modelos de IA Registrados y Compatibilidad Activa
print("\n--- 3. MODELOS DE IA ACTIVOS EN storage/ai_models ---")
models_dir = Path("C:/TradingBoot/smc_synthetic_bot/storage/ai_models")
for model_file in sorted(models_dir.glob("*.json")):
    if "_metrics" in model_file.name:
        continue
    try:
        content = json.loads(model_file.read_text(encoding="utf-8"))
        m_type = content.get("model_type", "LOGISTIC")
        samples = content.get("samples", 0)
        trained = content.get("trained", False)
        trained_at = content.get("trained_at", "")
        wr = content.get("provenance", {}).get("metrics", {}).get("base_win_rate") or content.get("positive_rate")
        wr_str = f"{wr*100:.1f}%" if wr else "N/A"
        print(f"• {model_file.name:<45} | Tipo: {m_type:<9} | Trained: {str(trained):<5} | Muestras: {samples:<6} | WR: {wr_str:<6} | {trained_at[:19]}")
    except Exception:
        pass

# 4. Candidatos Recientes de Malaysian SNR (msnr_candidates)
print("\n--- 4. ULTIMOS CANDIDATOS EVALUADOS (msnr_candidates) ---")
try:
    df_cand = pd.read_sql_query("""
        SELECT symbol, scenario, direction, first_seen, confirmed_at, first_reason, last_reason, executed
        FROM msnr_candidates
        ORDER BY id DESC LIMIT 8
    """, conn)
    if df_cand.empty:
        print("No hay candidatos registrados en msnr_candidates.")
    else:
        for idx, row in df_cand.iterrows():
            print(f"• {row['symbol']:<18} | {row['scenario']:<16} | {row['direction']:<5} | Ejecutado: {row['executed']} | Motivo: {row['first_reason']} -> {row['last_reason']}")
except Exception as exc:
    print(f"msnr_candidates info: {exc}")

conn.close()
