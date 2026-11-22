"""tools/operator/cmd_audit.py - Auditoría de confluencias, vetos y decisiones recientes."""

from __future__ import annotations

import argparse
import sys
from tools.operator.operator_db import get_recent_audit_events


def run_audit(symbol: str | None = None, limit: int = 10) -> int:
    events = get_recent_audit_events(symbol=symbol, limit=limit)

    print("=" * 75)
    print(f"      BLACKDAEMONFX — AUDITORÍA DE DECISIONES Y VETOS{' (' + symbol + ')' if symbol else ''}")
    print("=" * 75)

    if not events:
        print("  (No se encontraron eventos de auditoría registrados)")
    else:
        for ev in events:
            time_str = str(ev.get("event_time") or ev.get("created_at") or "")[:19]
            sym = str(ev.get("instrument") or "GLOBAL")
            action = str(ev.get("action") or ev.get("event_type") or "")
            reason = str(ev.get("reason") or "Sin motivo especificado")
            source = str(ev.get("source") or "LIVE")

            print(f"  [{time_str}] [{source}] {sym} -> {action}")
            print(f"      Motivo / Detalle: {reason}")
            print("  " + "-" * 71)

    print("=" * 75)
    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Auditoría de decisiones de trading")
    parser.add_argument("--symbol", "-s", type=str, default=None, help="Filtrar por símbolo")
    parser.add_argument("--limit", "-n", type=int, default=10, help="Número de eventos a mostrar")
    args = parser.parse_args()
    sys.exit(run_audit(symbol=args.symbol, limit=args.limit))
