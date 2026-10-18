"""
scratch/inspect_runner_heartbeat_and_logs.py
Inspección en modo de solo lectura de los logs y estado del runner en storage/runtime/
"""
import os
import sqlite3
from pathlib import Path
from datetime import datetime, timezone

PROJECT_ROOT = Path(__file__).resolve().parent.parent
STORAGE_RUNTIME = PROJECT_ROOT / "storage" / "runtime"

def main():
    print("=" * 100)
    print("INSPECCIÓN DE SOLO LECTURA: ESTADO Y ACTIVIDAD DEL RUNNER EN storage/runtime/")
    print("=" * 100)

    # 1. Listar archivos y timestamps de modificación
    if STORAGE_RUNTIME.exists():
        print("\nArchivos en storage/runtime/:")
        for p in sorted(STORAGE_RUNTIME.iterdir()):
            stat = p.stat()
            mtime = datetime.fromtimestamp(stat.st_mtime, timezone.utc).isoformat()
            size = stat.st_size
            print(f"  {p.name:35s} | Tamaño: {size:10,d} bytes | Última Modificación: {mtime}")
    else:
        print("No existe storage/runtime/")

    # 2. Inspeccionar shadow_events.jsonl (últimas líneas)
    jsonl_path = STORAGE_RUNTIME / "shadow_events.jsonl"
    if jsonl_path.exists():
        print("\nÚltimos 5 eventos en shadow_events.jsonl:")
        with open(jsonl_path, "r", encoding="utf-8", errors="replace") as f:
            lines = [l.strip() for l in f if l.strip()]
        for l in lines[-5:]:
            print("  ", l[:140])
        print(f"  Total líneas en shadow_events.jsonl: {len(lines)}")
        if lines:
            print("  Primer evento:", lines[0][:140])
            print("  Último evento:", lines[-1][:140])

    # 3. Inspeccionar shadow_research.sqlite3
    db_path = STORAGE_RUNTIME / "shadow_research.sqlite3"
    if db_path.exists():
        conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
        cur = conn.cursor()
        cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [r[0] for r in cur.fetchall()]
        print(f"\nTablas en shadow_research.sqlite3: {tables}")
        
        for t in tables:
            cur.execute(f"SELECT count(*) FROM {t}")
            cnt = cur.fetchone()[0]
            print(f"  Tabla '{t}': {cnt} registros")
            
        cur.execute("SELECT MIN(timestamp), MAX(timestamp) FROM shadow_signals")
        min_ts, max_ts = cur.fetchone()
        print(f"\nRango temporal en shadow_signals: {min_ts} a {max_ts}")
        
        # Últimas 5 señales por timestamp
        cur.execute("SELECT id, timestamp, strategy, variant, symbol, direction, market_outcome FROM shadow_signals ORDER BY id DESC LIMIT 5")
        latest_signals = cur.fetchall()
        print("\nÚltimas 5 señales registradas en shadow_signals:")
        for s in latest_signals:
            print("  ", s)
        conn.close()

if __name__ == '__main__':
    main()
