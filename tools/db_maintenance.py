"""Herramienta de mantenimiento y retención segura para la base SQLite de BlackDaemonFX.

Modo por defecto: `--dry-run` (solo lectura, reporta tamaño, páginas libres y filas
candidatas a purga sin modificar la base).

Con `--apply` (ejecutar preferentemente en ventana de mantenimiento 21:00–23:00 UTC):
- Elimina eventos antiguos (> `--retention-days`, default 30) de `daemon_audit_events`
  y `trade_audit_snapshots` (nunca toca `trades`, `trade_journal` ni `trade_visual_audits`).
- Ejecuta `PRAGMA wal_checkpoint(TRUNCATE)`.
- Opcionalmente ejecuta `VACUUM` con `--vacuum` para recuperar páginas freelist en disco.
"""

from __future__ import annotations

import argparse
from datetime import datetime, timedelta, timezone
from pathlib import Path
import sqlite3
import sys

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from database.database import resolve_db_path


RETENTION_TARGETS = (
    ("daemon_audit_events", "event_time"),
    ("trade_audit_snapshots", "snapshot_at"),
)
RETIRED_WORKERS = ("MALAYSIAN_SNR", "COMMODITIES_SNR", "FOREX_SNR")


def inspect_database(db_path: Path, retention_days: int = 30) -> dict:
    cutoff = (datetime.now(timezone.utc) - timedelta(days=max(1, int(retention_days)))).strftime(
        "%Y-%m-%d %H:%M:%S"
    )
    con = sqlite3.connect(f"file:{db_path.as_posix()}?mode=ro", uri=True, timeout=30)
    try:
        cur = con.cursor()
        page_count = int(cur.execute("PRAGMA page_count").fetchone()[0] or 0)
        page_size = int(cur.execute("PRAGMA page_size").fetchone()[0] or 4096)
        freelist_count = int(cur.execute("PRAGMA freelist_count").fetchone()[0] or 0)
        tables = {r[0] for r in cur.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()}

        targets = {}
        for table, time_col in RETENTION_TARGETS:
            if table not in tables:
                continue
            total = int(cur.execute(f'SELECT COUNT(*) FROM "{table}"').fetchone()[0] or 0)
            old_rows = int(
                cur.execute(
                    f'SELECT COUNT(*) FROM "{table}" WHERE "{time_col}" < ?',
                    (cutoff,),
                ).fetchone()[0]
                or 0
            )
            targets[table] = {"total_rows": total, "purgeable_rows": old_rows, "cutoff_utc": cutoff}

        stale_audit = {}
        if "trade_visual_audits" in tables:
            stale_audit["mt5_external_misattributed_visual_audits"] = int(
                cur.execute(
                    "SELECT COUNT(*) FROM trade_visual_audits "
                    "WHERE UPPER(COALESCE(source,''))='MT5_EXTERNAL' AND UPPER(COALESCE(bot_profile,''))!='MT5_EXTERNAL'"
                ).fetchone()[0]
                or 0
            )
        if "worker_runtime_states" in tables:
            placeholders = ",".join("?" for _ in RETIRED_WORKERS)
            stale_audit["retired_workers_stuck_running"] = int(
                cur.execute(
                    f"SELECT COUNT(*) FROM worker_runtime_states "
                    f"WHERE bot_profile IN ({placeholders}) AND status='RUNNING'",
                    RETIRED_WORKERS,
                ).fetchone()[0]
                or 0
            )

        return {
            "db_path": str(db_path),
            "total_mb": round((page_count * page_size) / 1e6, 2),
            "freelist_mb": round((freelist_count * page_size) / 1e6, 2),
            "freelist_pct": round((freelist_count / page_count) * 100.0, 2) if page_count else 0.0,
            "retention_days": int(retention_days),
            "cutoff_utc": cutoff,
            "targets": targets,
            "stale_audit": stale_audit,
        }
    finally:
        con.close()


def apply_maintenance(
    db_path: Path,
    retention_days: int = 30,
    run_vacuum: bool = False,
    clean_stale_audit: bool = False,
) -> dict:
    cutoff = (datetime.now(timezone.utc) - timedelta(days=max(1, int(retention_days)))).strftime(
        "%Y-%m-%d %H:%M:%S"
    )
    deleted = {}
    cleaned = {}
    con = sqlite3.connect(str(db_path), timeout=60)
    try:
        cur = con.cursor()
        cur.execute("PRAGMA busy_timeout=60000")
        tables = {r[0] for r in cur.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()}
        for table, time_col in RETENTION_TARGETS:
            if table not in tables:
                continue
            cur.execute(f'DELETE FROM "{table}" WHERE "{time_col}" < ?', (cutoff,))
            deleted[table] = int(cur.rowcount or 0)
        if clean_stale_audit:
            if "trade_visual_audits" in tables:
                cur.execute(
                    "UPDATE trade_visual_audits SET bot_profile='MT5_EXTERNAL', daemon_magic=0 "
                    "WHERE UPPER(COALESCE(source,''))='MT5_EXTERNAL' AND UPPER(COALESCE(bot_profile,''))!='MT5_EXTERNAL'"
                )
                cleaned["trade_visual_audits_reattributed"] = int(cur.rowcount or 0)
            if "worker_runtime_states" in tables:
                placeholders = ",".join("?" for _ in RETIRED_WORKERS)
                cur.execute(
                    f"UPDATE worker_runtime_states SET status='STOPPED', last_action='RETIRED_WORKER_CLEANUP' "
                    f"WHERE bot_profile IN ({placeholders}) AND status='RUNNING'",
                    RETIRED_WORKERS,
                )
                cleaned["retired_workers_stopped"] = int(cur.rowcount or 0)
        con.commit()
        cur.execute("PRAGMA wal_checkpoint(TRUNCATE)")
        if run_vacuum:
            cur.execute("VACUUM")
    finally:
        con.close()
    after = inspect_database(db_path, retention_days=retention_days)
    after["deleted"] = deleted
    after["cleaned"] = cleaned
    after["vacuum_executed"] = bool(run_vacuum)
    return after


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Mantenimiento y retención segura de SQLite BlackDaemonFX")
    parser.add_argument("--db", type=str, default=None, help="Ruta explícita a trading_bot.sqlite3")
    parser.add_argument("--retention-days", type=int, default=30, help="Días de retención (default: 30)")
    parser.add_argument("--apply", action="store_true", help="Ejecuta la purga (sin este flag solo hace dry-run)")
    parser.add_argument("--vacuum", action="store_true", help="Ejecuta VACUUM tras la purga (solo con --apply)")
    parser.add_argument(
        "--clean-stale-audit",
        action="store_true",
        help="Corrige atribución histórica MT5_EXTERNAL en trade_visual_audits y marca STOPPED workers retirados",
    )
    args = parser.parse_args(argv)

    db_path = resolve_db_path(args.db)
    if not db_path.exists():
        print(f"ERROR: No existe la base de datos en {db_path}")
        return 1

    if not args.apply:
        report = inspect_database(db_path, retention_days=args.retention_days)
        print("[DRY-RUN] Estado actual (sin cambios):")
        print(report)
        return 0

    report = apply_maintenance(
        db_path,
        retention_days=args.retention_days,
        run_vacuum=args.vacuum,
        clean_stale_audit=args.clean_stale_audit,
    )
    print("[APPLIED] Mantenimiento completado:")
    print(report)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
