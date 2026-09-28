"""Instalador seguro del hotfix v115 sobre DaemonBlackFx v114."""

from __future__ import annotations

import argparse
import ast
from datetime import datetime
from pathlib import Path
import shutil


VERSION = "v115-h4-smc-deriv-lock-watchdog-fix"
PAYLOAD_FILES = (
    "strategy/execution/multi_timeframe.py",
    "strategy/execution/live_trading_engine.py",
    "reporting/console_reporting_service.py",
    "dashboard/realtime_dashboard.py",
    "marketdata/rate_limit.py",
    "daemon_version.py",
)


def patch_coordinator(source: str) -> tuple[str, bool]:
    marker = "worker_progress_fingerprints = {}"
    if marker in source:
        return source, False

    declaration = "    worker_started_at = {}\n    worker_stall_warning_at = {}"
    if declaration not in source:
        raise RuntimeError("No se encontró el watchdog v114 esperado en app/main.py")
    source = source.replace(
        declaration,
        "    worker_started_at = {}\n"
        "    worker_progress_fingerprints = {}\n"
        "    worker_last_progress_at = {}\n"
        "    worker_stall_warning_at = {}",
        1,
    )

    startup = "            worker_started_at[profile] = time.monotonic()"
    if startup not in source:
        raise RuntimeError("No se encontró la inicialización del watchdog v114")
    source = source.replace(
        startup,
        startup
        + "\n            worker_progress_fingerprints.pop(profile, None)"
        + "\n            worker_last_progress_at[profile] = time.monotonic()",
        1,
    )

    watchdog_start = source.find(
        "                    # Un proceso puede seguir vivo y quedar detenido dentro de"
    )
    heartbeat_start = source.find(
        "                    try:\n                        existing = {",
        watchdog_start,
    )
    if watchdog_start < 0 or heartbeat_start < 0:
        raise RuntimeError("No se pudo aislar el watchdog de log v114")
    source = source[:watchdog_start] + source[heartbeat_start:]

    needle = """                        }.get(profile, {})
                        repo.upsert_worker_runtime_state("""
    if needle not in source:
        raise RuntimeError("No se encontró el heartbeat del worker v114")
    progress_guard = """                        }.get(profile, {})

                        # El progreso se mide con telemetría del propio worker,
                        # no con mtime del log: stdout se almacena en bloques en
                        # Windows y puede permanecer sin cambios varios minutos.
                        fingerprint = (
                            existing.get("cycle_number"),
                            existing.get("status"),
                            existing.get("symbols_processed"),
                            existing.get("symbols_total"),
                            existing.get("current_symbol"),
                            existing.get("last_action"),
                            existing.get("last_reason"),
                        )
                        if worker_progress_fingerprints.get(profile) != fingerprint:
                            worker_progress_fingerprints[profile] = fingerprint
                            worker_last_progress_at[profile] = now

                        progress_age = now - worker_last_progress_at.get(
                            profile, worker_started_at.get(profile, now)
                        )
                        stall_timeout = max(
                            60.0,
                            float(os.getenv(
                                "DAEMON_WORKER_STALL_TIMEOUT_SECONDS", "300"
                            )),
                        )
                        if progress_age >= stall_timeout:
                            open_positions = []
                            for trade in repo.open_trades(source="DEMO") or []:
                                details = trade.get("details") if isinstance(trade, dict) else {}
                                metadata = details.get("metadata") if isinstance(details, dict) else {}
                                if str(metadata.get("bot_profile") or "").upper() == profile:
                                    open_positions.append(trade)
                            last_warning = worker_stall_warning_at.get(profile, 0.0)
                            if now - last_warning >= 60.0:
                                worker_stall_warning_at[profile] = now
                                reason = (
                                    f"Sin avance de telemetría durante {progress_age:.0f}s; "
                                    f"posiciones_abiertas={len(open_positions)}"
                                )
                                print(f"[WORKER STALL] {profile}: {reason}", file=sys.stderr)
                                try:
                                    repo.save_audit_event(
                                        "BOT_WORKER_STALLED",
                                        source="DEMO",
                                        action=(
                                            "STALL_RESTART_REQUESTED"
                                            if not open_positions
                                            else "STALL_RESTART_BLOCKED_OPEN_POSITIONS"
                                        ),
                                        reason=profile,
                                        payload={
                                            "profile": profile,
                                            "pid": proc.pid,
                                            "progress_age_seconds": progress_age,
                                            "open_positions": len(open_positions),
                                        },
                                    )
                                except Exception:
                                    pass
                            if not open_positions:
                                proc.terminate()
                                continue

                        repo.upsert_worker_runtime_state("""
    source = source.replace(needle, progress_guard, 1)

    cleanup = """                worker_stall_warning_at.pop(profile, None)
                worker_started_at.pop(profile, None)"""
    if cleanup not in source:
        raise RuntimeError("No se encontró la limpieza del watchdog v114")
    source = source.replace(
        cleanup,
        cleanup
        + "\n                worker_progress_fingerprints.pop(profile, None)"
        + "\n                worker_last_progress_at.pop(profile, None)",
        1,
    )
    ast.parse(source)
    return source, True


def install(project: Path) -> None:
    project = project.resolve()
    payload = Path(__file__).resolve().parent / "payload"
    version_file = project / "daemon_version.py"
    app_file = project / "app" / "main.py"
    if not version_file.is_file() or not app_file.is_file():
        raise SystemExit(f"No parece un proyecto DaemonBlackFx válido: {project}")
    current = version_file.read_text(encoding="utf-8", errors="replace")
    if "v114-deriv-rate-limit-recovery" not in current and VERSION not in current:
        raise SystemExit(
            "Actualización bloqueada: instale primero v114-deriv-rate-limit-recovery."
        )

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup = project / "storage" / "update_backups" / f"pre_v115_{timestamp}"
    targets = [app_file] + [project / relative for relative in PAYLOAD_FILES]
    for target in targets:
        if not target.is_file():
            raise SystemExit(f"Falta archivo requerido en v114: {target}")
        relative = target.relative_to(project)
        destination = backup / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(target, destination)

    app_source = app_file.read_text(encoding="utf-8")
    patched, changed = patch_coordinator(app_source)
    if changed:
        app_file.write_text(patched, encoding="utf-8", newline="")

    for relative in PAYLOAD_FILES:
        source_file = payload / relative
        destination = project / relative
        if not source_file.is_file():
            raise SystemExit(f"Payload incompleto: {source_file}")
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source_file, destination)

    for relative in ("app/main.py",) + PAYLOAD_FILES:
        if str(relative).endswith(".py"):
            ast.parse((project / relative).read_text(encoding="utf-8"))

    print("ACTUALIZACIÓN COMPLETADA")
    print(f"Versión: {VERSION}")
    print(f"Respaldo: {backup}")
    print("Reinicie el daemon y verifique la versión antes de ejecutar.")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--project", default=".")
    args = parser.parse_args()
    install(Path(args.project))


if __name__ == "__main__":
    main()
