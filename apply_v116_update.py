"""Instalador seguro de la auditoría visual Deriv v116 sobre v115."""

from __future__ import annotations

import argparse
import ast
from datetime import datetime
from pathlib import Path
import shutil


VERSION = "v116-deriv-annotated-trade-audit"
REQUIRED_VERSION = "v115-h4-smc-deriv-lock-watchdog-fix"
PAYLOAD_FILES = (
    "dashboard/trade_audit_page.py",
    "dashboard/realtime_dashboard.py",
    "strategy/execution/live_trading_engine.py",
    "strategy/orb/new_york_orb.py",
    "daemon_version.py",
)


def install(project: Path) -> None:
    project = project.resolve()
    payload = Path(__file__).resolve().parent / "payload"
    version_file = project / "daemon_version.py"
    if not version_file.is_file():
        raise SystemExit(f"No parece un proyecto DaemonBlackFx válido: {project}")
    current = version_file.read_text(encoding="utf-8", errors="replace")
    if REQUIRED_VERSION not in current and VERSION not in current:
        raise SystemExit(
            f"Actualización bloqueada: se requiere {REQUIRED_VERSION}."
        )

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup = project / "storage" / "update_backups" / f"pre_v116_{timestamp}"
    for relative in PAYLOAD_FILES:
        target = project / relative
        source = payload / relative
        if not target.is_file():
            raise SystemExit(f"Falta archivo requerido en v115: {target}")
        if not source.is_file():
            raise SystemExit(f"Payload incompleto: {source}")
        destination = backup / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(target, destination)

    for relative in PAYLOAD_FILES:
        source = payload / relative
        destination = project / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, destination)
        if destination.suffix == ".py":
            ast.parse(destination.read_text(encoding="utf-8"))

    print("ACTUALIZACIÓN COMPLETADA")
    print(f"Versión: {VERSION}")
    print(f"Respaldo: {backup}")
    print("Reinicie el daemon y abra una auditoría desde /account.")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--project", default=".")
    args = parser.parse_args()
    install(Path(args.project))


if __name__ == "__main__":
    main()
