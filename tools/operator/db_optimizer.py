"""tools/operator/db_optimizer.py - Utilidad de optimización y mantenimiento de SQLite.

Diseñado para:
1. Inspeccionar tamaño, fragmentación y páginas libres (freelist) de la base viva.
2. Ejecutar checkpoint WAL no bloqueante (PASSIVE / FULL) sin congelar workers.
3. Podar eventos efímeros de telemetría (daemon_audit_events, trade_audit_snapshots)
   preservando el 100% de trades, señales y diario operativo.
4. Actualizar estadísticas del optimizador de consultas de SQLite (PRAGMA optimize).
"""

from __future__ import annotations

import argparse
import os
from pathlib import Path
import sqlite3
from typing import Any, Dict, Optional

from tools.operator.operator_db import resolve_database_path


def get_db_storage_stats(db_path: Optional[Path] = None) -> Dict[str, Any]:
    """Obtiene métricas de almacenamiento, páginas y fragmentación de SQLite."""
    path = Path(db_path) if db_path else resolve_database_path()
    if not path.exists():
        return {"error": f"Base de datos no encontrada: {path}"}

    file_size_bytes = path.stat().st_size
    wal_path = path.with_name(path.name + "-wal")
    wal_size_bytes = wal_path.stat().st_size if wal_path.exists() else 0

    conn = sqlite3.connect(f"file:{path.as_posix()}?mode=ro", uri=True, timeout=5.0)
    try:
        cur = conn.cursor()
        cur.execute("PRAGMA page_count;")
        page_count = int(cur.fetchone()[0] or 0)
        cur.execute("PRAGMA page_size;")
        page_size = int(cur.fetchone()[0] or 4096)
        cur.execute("PRAGMA freelist_count;")
        freelist_count = int(cur.fetchone()[0] or 0)

        reclaimable_bytes = freelist_count * page_size
        reclaimable_mb = round(reclaimable_bytes / (1024 * 1024), 2)
        total_mb = round(file_size_bytes / (1024 * 1024), 2)
        wal_mb = round(wal_size_bytes / (1024 * 1024), 2)

        # Conteo rápido de tablas operativas
        cur.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = [r[0] for r in cur.fetchall()]
        table_counts = {}
        for tbl in ("trades", "trade_journal", "daemon_audit_events", "trade_audit_snapshots", "msnr_candidates"):
            if tbl in tables:
                cur.execute(f"SELECT COUNT(*) FROM {tbl};")
                table_counts[tbl] = int(cur.fetchone()[0] or 0)

        return {
            "db_path": str(path),
            "total_bytes": file_size_bytes,
            "total_mb": total_mb,
            "wal_mb": wal_mb,
            "page_count": page_count,
            "page_size": page_size,
            "freelist_pages": freelist_count,
            "reclaimable_mb": reclaimable_mb,
            "fragmentation_percent": round((reclaimable_bytes / file_size_bytes * 100.0), 2) if file_size_bytes > 0 else 0.0,
            "table_counts": table_counts,
        }
    finally:
        conn.close()


def run_passive_checkpoint(db_path: Optional[Path] = None) -> Dict[str, Any]:
    """Ejecuta un checkpoint WAL en modo PASSIVE (cero interferencia con workers)."""
    path = Path(db_path) if db_path else resolve_database_path()
    conn = sqlite3.connect(str(path), timeout=10.0)
    try:
        cur = conn.cursor()
        cur.execute("PRAGMA busy_timeout=10000;")
        cur.execute("PRAGMA wal_checkpoint(PASSIVE);")
        row = cur.fetchone()
        cur.execute("PRAGMA optimize;")
        return {
            "status": "OK",
            "busy": int(row[0]) if row else 0,
            "wal_pages": int(row[1]) if row else 0,
            "checkpointed_pages": int(row[2]) if row else 0,
        }
    finally:
        conn.close()


def ensure_performance_optimizations(db_path: Optional[Path] = None) -> Dict[str, Any]:
    """Aplica índices compuestos críticos y pragmas de alto rendimiento."""
    path = Path(db_path) if db_path else resolve_database_path()
    conn = sqlite3.connect(str(path), timeout=15.0)
    try:
        cur = conn.cursor()
        cur.execute("PRAGMA busy_timeout=30000;")
        cur.execute("PRAGMA synchronous=NORMAL;")
        cur.execute("PRAGMA mmap_size=536870912;")
        cur.execute("CREATE INDEX IF NOT EXISTS ix_audit_action_time ON daemon_audit_events (action, event_time);")
        cur.execute("CREATE INDEX IF NOT EXISTS ix_audit_type_action_time ON daemon_audit_events (event_type, action, event_time);")
        cur.execute("PRAGMA optimize;")
        conn.commit()
        return {"status": "OK", "indexes_ensured": True, "synchronous": "NORMAL", "mmap_mb": 512}
    finally:
        conn.close()


def prune_ephemeral_telemetry(db_path: Optional[Path] = None, retention_days: int = 3) -> Dict[str, Any]:
    """Purga eventos de telemetría efímeros (CYCLE_START) preservando todas las auditorías y decisiones."""
    path = Path(db_path) if db_path else resolve_database_path()
    conn = sqlite3.connect(str(path), timeout=20.0)
    try:
        cur = conn.cursor()
        cur.execute("PRAGMA busy_timeout=30000;")
        # Contar cuántos eventos CYCLE_START hay con más de retention_days
        cur.execute("""
            SELECT COUNT(*) FROM daemon_audit_events
            WHERE event_type = 'CYCLE_START'
              AND event_time < datetime('now', ? || ' days')
        """, (f"-{retention_days}",))
        to_delete = cur.fetchone()[0] or 0

        deleted = 0
        if to_delete > 0:
            cur.execute("""
                DELETE FROM daemon_audit_events
                WHERE event_type = 'CYCLE_START'
                  AND event_time < datetime('now', ? || ' days')
            """, (f"-{retention_days}",))
            deleted = cur.rowcount
            conn.commit()

        cur.execute("PRAGMA optimize;")
        return {
            "status": "OK",
            "retention_days": retention_days,
            "ephemeral_events_pruned": deleted,
        }
    finally:
        conn.close()


def vacuum_database(db_path: Optional[Path] = None, timeout: float = 180.0) -> Dict[str, Any]:
    """Ejecuta VACUUM completo para desfragmentar y recuperar páginas libres (freelist).

    ADVERTENCIA: Requiere bloqueo exclusivo. Debe ejecutarse preferentemente durante
    la ventana de mantenimiento diario (21:00-23:00 UTC) con daemons en reposo o detenidos.
    """
    path = Path(db_path) if db_path else resolve_database_path()
    size_before = path.stat().st_size if path.exists() else 0

    conn = sqlite3.connect(str(path), timeout=timeout)
    try:
        cur = conn.cursor()
        cur.execute(f"PRAGMA busy_timeout={int(timeout * 1000)};")
        cur.execute("VACUUM;")
        cur.execute("PRAGMA optimize;")
        conn.commit()

        size_after = path.stat().st_size if path.exists() else 0
        reclaimed_mb = round((size_before - size_after) / (1024 * 1024), 2)
        return {
            "status": "OK",
            "size_before_mb": round(size_before / (1024 * 1024), 2),
            "size_after_mb": round(size_after / (1024 * 1024), 2),
            "reclaimed_mb": reclaimed_mb,
        }
    finally:
        conn.close()


def main():
    parser = argparse.ArgumentParser(description="Optimizador y diagnóstico de almacenamiento de SQLite.")
    parser.add_argument("--stats", action="store_true", help="Muestra estadísticas de almacenamiento y fragmentación.")
    parser.add_argument("--checkpoint", action="store_true", help="Ejecuta checkpoint WAL PASSIVE y PRAGMA optimize.")
    parser.add_argument("--optimize", action="store_true", help="Aplica índices compuestos y PRAGMAs de alto rendimiento.")
    parser.add_argument("--prune-ephemeral", action="store_true", help="Purga eventos CYCLE_START efímeros antiguos (>3 días).")
    parser.add_argument("--days", type=int, default=3, help="Días de retención para eventos efímeros.")
    parser.add_argument("--vacuum", action="store_true", help="Ejecuta VACUUM (ventana de mantenimiento 21:00-23:00 UTC).")
    args = parser.parse_args()

    if args.optimize:
        res = ensure_performance_optimizations()
        print("\n=== OPTIMIZACIÓN DE ÍNDICES Y PRAGMAS ===")
        print(f"Resultado: {res}")

    if args.prune_ephemeral:
        res = prune_ephemeral_telemetry(retention_days=args.days)
        print("\n=== PURGA DE TELEMETRÍA EFÍMERA ===")
        print(f"Resultado: {res}")

    if args.vacuum:
        print("\n=== EJECUTANDO VACUUM (COMPACTACIÓN DE ALMACENAMIENTO) ===")
        res = vacuum_database()
        print(f"Resultado: {res}")

    if args.checkpoint:
        res = run_passive_checkpoint()
        print("\n=== CHECKPOINT WAL EJECUTADO ===")
        print(f"Resultado: {res}")

    if args.stats or not (args.checkpoint or args.optimize or args.prune_ephemeral or args.vacuum):
        stats = get_db_storage_stats()
        print("=== ESTADÍSTICAS DE ALMACENAMIENTO SQLITE ===")
        print(f"Ruta: {stats.get('db_path')}")
        print(f"Tamaño archivo principal: {stats.get('total_mb')} MB")
        print(f"Tamaño archivo WAL: {stats.get('wal_mb')} MB")
        print(f"Páginas libres (freelist): {stats.get('freelist_pages')} ({stats.get('reclaimable_mb')} MB recuperables)")
        print(f"Fragmentación estimada: {stats.get('fragmentation_percent')}%")
        print("Filas por tabla:")
        for tbl, cnt in (stats.get("table_counts") or {}).items():
            print(f"  - {tbl}: {cnt:,} filas")


if __name__ == "__main__":
    main()
