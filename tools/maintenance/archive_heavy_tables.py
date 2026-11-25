"""Script de mantenimiento industrial y archivo seguro de tablas pesadas de SQLite.

Diseñado para bases de datos de alta concurrencia (17 workers operando en vivo):
1. Archiva registros de auditoría y telemetría efímera más antiguos que N días
   hacia `storage/live_trading_archive.sqlite3`.
2. Preserva al 100% las tablas críticas de negocio: `trades`, `trade_journal`,
   `signals`, `trade_visual_audits`, `worker_runtime_states`, configuraciones y candidatos.
3. Opera en lotes acotados (chunks) con micro-pausas anti-contención para no
   monopolizar el archivo y permitir que los daemons escriban sin bloqueos.
4. Ejecuta checkpoint WAL y optimización de páginas.
"""

from __future__ import annotations

import argparse
import datetime
import os
import sqlite3
import sys
import time
from typing import Dict, List, Tuple


# Configuración de retención por tabla (días a conservar en base viva)
DEFAULT_RETENTION_DAYS = {
    "daemon_audit_events": 7,          # Eventos de auditoría de daemon (611k filas)
    "trade_audit_snapshots": 7,        # Snapshots de auditoría periódica
    "msnr_candidate_transitions": 7,   # Transiciones de estado MSNR efímeras
    "account_snapshots": 14,           # Snapshots de balance/equity (2 semanas)
}

# Tablas estrictamente protegidas que NUNCA se tocan
PROTECTED_TABLES = {
    "trades",
    "trade_journal",
    "signals",
    "trade_visual_audits",
    "position_visual_audits",
    "worker_runtime_states",
    "msnr_candidates",
    "msnr_candidate_outcomes",
    "msnr_model_registry",
    "instrument_selection_preferences",
    "instrument_selection_profile_preferences",
    "daily_profit_target_preferences",
    "strategy_runtime_preferences",
    "account_stats_resets",
}


def get_table_schema(conn: sqlite3.Connection, table_name: str) -> str | None:
    cur = conn.cursor()
    cur.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name=?", (table_name,))
    row = cur.fetchone()
    return row[0] if row else None


def ensure_archive_table(archive_conn: sqlite3.Connection, live_conn: sqlite3.Connection, table_name: str) -> None:
    schema_sql = get_table_schema(live_conn, table_name)
    if not schema_sql:
        return
    cur = archive_conn.cursor()
    cur.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (table_name,))
    if not cur.fetchone():
        cur.execute(schema_sql)
        archive_conn.commit()


def archive_and_purge_table(
    live_conn: sqlite3.Connection,
    archive_conn: sqlite3.Connection,
    table_name: str,
    retention_days: int,
    batch_size: int = 2500,
    sleep_between_batches: float = 0.05,
    dry_run: bool = False,
) -> Tuple[int, int]:
    """Archiva y purga una tabla en lotes seguros sin bloquear los daemons."""
    if table_name in PROTECTED_TABLES:
        print(f"[-] Omitiendo tabla protegida: {table_name}")
        return 0, 0

    ensure_archive_table(archive_conn, live_conn, table_name)

    now_utc = datetime.datetime.now(datetime.timezone.utc)
    cutoff_time = (now_utc - datetime.timedelta(days=retention_days)).isoformat()

    live_cur = live_conn.cursor()
    archive_cur = archive_conn.cursor()

    # Determinar columna temporal de la tabla priorizando columnas con índice B-Tree
    live_cur.execute(f"PRAGMA table_info({table_name})")
    cols = [r[1] for r in live_cur.fetchall()]
    if "event_time" in cols:
        time_col = "event_time"
    elif "snapshot_at" in cols:
        time_col = "snapshot_at"
    elif "snapshot_time" in cols:
        time_col = "snapshot_time"
    elif "created_at" in cols:
        time_col = "created_at"
    elif "observed_at" in cols:
        time_col = "observed_at"
    else:
        print(f"[!] Tabla {table_name} no tiene columna temporal conocida ({cols}). Omitiendo.", flush=True)
        return 0, 0

    col_names_str = ", ".join(f'"{c}"' for c in cols)
    placeholders_str = ", ".join("?" for _ in cols)

    # Identificar filas a archivar
    live_cur.execute(f'SELECT count(*) FROM "{table_name}" WHERE "{time_col}" < ?', (cutoff_time,))
    total_eligible = live_cur.fetchone()[0]
    print(f"[*] {table_name}: {total_eligible:,} filas elegibles para archivo (< {retention_days}d, columna: {time_col}, corte: {cutoff_time[:19]}).", flush=True)

    if total_eligible == 0:
        return 0, 0

    if dry_run:
        return total_eligible, 0

    archived_count = 0
    while True:
        # Extraer lote de IDs antiguos
        live_cur.execute(
            f'SELECT id FROM "{table_name}" WHERE "{time_col}" < ? ORDER BY id ASC LIMIT ?',
            (cutoff_time, batch_size),
        )
        id_rows = live_cur.fetchall()
        if not id_rows:
            break

        ids = [r[0] for r in id_rows]
        id_placeholders = ", ".join("?" for _ in ids)

        # Leer filas completas del lote
        live_cur.execute(
            f'SELECT {col_names_str} FROM "{table_name}" WHERE id IN ({id_placeholders})',
            ids,
        )
        batch_data = live_cur.fetchall()

        # Insertar en base de archivo
        archive_cur.executemany(
            f'INSERT OR IGNORE INTO "{table_name}" ({col_names_str}) VALUES ({placeholders_str})',
            batch_data,
        )
        archive_conn.commit()

        # Borrar lote de la base viva
        live_cur.execute(
            f'DELETE FROM "{table_name}" WHERE id IN ({id_placeholders})',
            ids,
        )
        live_conn.commit()

        archived_count += len(ids)
        pct = round(archived_count * 100.0 / total_eligible, 1)
        print(f"    --> {table_name}: {archived_count:,} / {total_eligible:,} filas ({pct}%) archivadas y purgadas.")

        if sleep_between_batches > 0:
            time.sleep(sleep_between_batches)

    return total_eligible, archived_count


def run_maintenance(
    live_db_path: str = "storage/live_trading_bot.sqlite3",
    archive_db_path: str = "storage/live_trading_archive.sqlite3",
    retention_overrides: Dict[str, int] | None = None,
    batch_size: int = 2500,
    sleep_between_batches: float = 0.05,
    do_vacuum: bool = True,
    dry_run: bool = False,
) -> dict:
    start_time = time.time()
    retention = dict(DEFAULT_RETENTION_DAYS)
    if retention_overrides:
        retention.update(retention_overrides)

    if not os.path.exists(live_db_path):
        print(f"[!] Error: La base viva {live_db_path} no existe.")
        return {"error": "FILE_NOT_FOUND"}

    orig_size_bytes = os.path.getsize(live_db_path)
    orig_size_mb = round(orig_size_bytes / (1024 * 1024), 2)
    print(f"=== Mantenimiento Seguro de SQLite BlackDaemonFX ===")
    print(f"Base viva: {live_db_path} ({orig_size_mb} MB)")
    print(f"Base archivo: {archive_db_path}")
    print(f"Modo Dry-Run: {dry_run}")
    print("-----------------------------------------------------")

    # Conectar con timeouts holgados
    live_conn = sqlite3.connect(live_db_path, timeout=60.0)
    live_conn.execute("PRAGMA busy_timeout = 60000")

    archive_conn = sqlite3.connect(archive_db_path, timeout=60.0)
    archive_conn.execute("PRAGMA journal_mode = WAL")
    archive_conn.execute("PRAGMA synchronous = NORMAL")

    results = {}
    total_purged = 0

    try:
        for tbl, ret_days in retention.items():
            eligible, purged = archive_and_purge_table(
                live_conn=live_conn,
                archive_conn=archive_conn,
                table_name=tbl,
                retention_days=ret_days,
                batch_size=batch_size,
                sleep_between_batches=sleep_between_batches,
                dry_run=dry_run,
            )
            results[tbl] = {"eligible": eligible, "purged": purged, "retention_days": ret_days}
            total_purged += purged

        # WAL Checkpoint
        if not dry_run and total_purged > 0:
            print("[*] Ejecutando PRAGMA wal_checkpoint(TRUNCATE)...")
            try:
                live_conn.execute("PRAGMA wal_checkpoint(TRUNCATE)")
            except Exception as e:
                print(f"[!] Aviso checkpoint: {e}")

        # Compactación y recuperación física de espacio
        vacuum_done = False
        if not dry_run and do_vacuum and total_purged > 0:
            print("[*] Ejecutando VACUUM para recuperar espacio en disco y desfragmentar páginas...")
            try:
                vacuum_t0 = time.time()
                live_conn.execute("VACUUM")
                vacuum_elapsed = round(time.time() - vacuum_t0, 2)
                vacuum_done = True
                print(f"[+] VACUUM completado exitosamente en {vacuum_elapsed}s.")
            except Exception as exc:
                print(f"[!] Error ejecutando VACUUM (posible contención de locks): {exc}")
                print("[*] Sugerencia: El espacio libre queda en el freelist interno y se reutilizará automáticamente.")

        live_conn.execute("PRAGMA optimize")

    finally:
        live_conn.close()
        archive_conn.close()

    new_size_bytes = os.path.getsize(live_db_path)
    new_size_mb = round(new_size_bytes / (1024 * 1024), 2)
    saved_mb = round(orig_size_mb - new_size_mb, 2)
    archive_size_mb = round(os.path.getsize(archive_db_path) / (1024 * 1024), 2) if os.path.exists(archive_db_path) else 0.0
    elapsed_total = round(time.time() - start_time, 2)

    summary = {
        "original_size_mb": orig_size_mb,
        "new_size_mb": new_size_mb,
        "saved_mb": saved_mb,
        "archive_size_mb": archive_size_mb,
        "total_purged_rows": total_purged,
        "tables": results,
        "vacuum_done": vacuum_done,
        "elapsed_seconds": elapsed_total,
    }

    print("-----------------------------------------------------")
    print(f"[✓] Mantenimiento finalizado en {elapsed_total}s.")
    print(f"    Filas totales archivadas y purgadas: {total_purged:,}")
    print(f"    Tamaño inicial: {orig_size_mb} MB")
    print(f"    Tamaño final:   {new_size_mb} MB")
    print(f"    Espacio liberado en disco: {saved_mb} MB ({round((saved_mb/orig_size_mb)*100, 1) if orig_size_mb else 0}%)")
    print(f"    Tamaño base de archivo histórico: {archive_size_mb} MB")

    return summary


def main():
    parser = argparse.ArgumentParser(description="Mantenimiento seguro y rotación de SQLite")
    parser.add_argument("--live-db", default="storage/live_trading_bot.sqlite3", help="Ruta a base viva")
    parser.add_argument("--archive-db", default="storage/live_trading_archive.sqlite3", help="Ruta a base de archivo")
    parser.add_argument("--days", type=int, default=7, help="Días de retención para tablas de auditoría")
    parser.add_argument("--batch-size", type=int, default=2500, help="Tamaño de lote")
    parser.add_argument("--no-vacuum", action="store_true", help="Omitir VACUUM")
    parser.add_argument("--dry-run", action="store_true", help="Solo contar registros sin modificar")
    args = parser.parse_args()

    retention_overrides = {
        "daemon_audit_events": args.days,
        "trade_audit_snapshots": args.days,
        "msnr_candidate_transitions": args.days,
        "account_snapshots": max(14, args.days * 2),
    }

    run_maintenance(
        live_db_path=args.live_db,
        archive_db_path=args.archive_db,
        retention_overrides=retention_overrides,
        batch_size=args.batch_size,
        do_vacuum=not args.no_vacuum,
        dry_run=args.dry_run,
    )


if __name__ == "__main__":
    main()
