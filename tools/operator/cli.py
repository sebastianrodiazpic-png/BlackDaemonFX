"""tools/operator/cli.py - Despachador unificado de comandos del Operador BlackDaemonFX.

Uso:
    python -m tools.operator.cli status
    python -m tools.operator.cli audit [--symbol XAUUSD] [--limit 10]
    python -m tools.operator.cli macro
    python -m tools.operator.cli catalog
"""

from __future__ import annotations

import argparse
import sys
from tools.operator.cmd_status import run_status
from tools.operator.cmd_audit import run_audit
from tools.operator.cmd_macro import run_macro
from tools.operator.cmd_catalog import run_catalog


def main() -> int:
    parser = argparse.ArgumentParser(
        prog="operator",
        description="Suite interactiva del Operador de BlackDaemonFX"
    )
    subparsers = parser.add_subparsers(dest="command", help="Comandos disponibles")

    # status
    subparsers.add_parser("status", help="Muestra el estado del bot, ciclo y posiciones abiertas")

    # audit
    audit_parser = subparsers.add_parser("audit", help="Auditoría de vetos, confluencias y decisiones")
    audit_parser.add_argument("--symbol", "-s", type=str, default=None, help="Filtrar por símbolo")
    audit_parser.add_argument("--limit", "-n", type=int, default=10, help="Límite de eventos")

    # macro
    subparsers.add_parser("macro", help="Radar macroeconómico y eventos de alto impacto")

    # catalog
    subparsers.add_parser("catalog", help="Resumen del catálogo de 212 pares y poda preventiva")

    args = parser.parse_args()

    if args.command == "status":
        return run_status()
    elif args.command == "audit":
        return run_audit(symbol=args.symbol, limit=args.limit)
    elif args.command == "macro":
        return run_macro()
    elif args.command == "catalog":
        return run_catalog()
    else:
        parser.print_help()
        return 0


if __name__ == "__main__":
    sys.exit(main())
