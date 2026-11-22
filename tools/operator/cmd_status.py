"""tools/operator/cmd_status.py - Muestra el estado operativo de BlackDaemonFX."""

from __future__ import annotations

import sys
from tools.operator.operator_db import get_system_status, get_open_positions


def run_status() -> int:
    status = get_system_status()
    positions = get_open_positions()

    print("=" * 65)
    print("      BLACKDAEMONFX — ESTADO OPERATIVO DEL SISTEMA")
    print("=" * 65)
    print(f"  Estado del Bot:       {status['bot_status']}")
    print(f"  Modo de Conexión:     {status['connection_mode']}")
    print(f"  Frescura de Datos:    {status['data_freshness']}")
    print(f"  Ciclo Actual:         #{status['cycle']}")
    print(f"  Símbolos Escaneados:  {status['symbols_processed']} / {status['symbols_total']}")
    print(f"  Última Actualización: {status['last_update'] or 'N/A'}")
    print(f"  Base de Datos (RO):   {status['db_path']}")
    print("-" * 65)
    print(f"  POSICIONES ABIERTAS: {len(positions)}")

    if not positions:
        print("  (No hay posiciones abiertas en este momento)")
    else:
        print(f"  {'TICKET':<10} {'SÍMBOLO':<18} {'DIR':<6} {'PRECIO':<10} {'SL':<10} {'TP':<10} {'RR':<6}")
        print("  " + "-" * 63)
        for p in positions:
            ticket = str(p.get("broker_position_ticket") or p.get("id"))
            sym = str(p.get("instrument") or "")[:17]
            direction = str(p.get("direction") or "")[:5]
            entry = f"{float(p.get('entry_price') or 0.0):.5f}"[:9]
            sl = f"{float(p.get('stop_loss') or 0.0):.5f}"[:9]
            tp = f"{float(p.get('take_profit') or 0.0):.5f}"[:9]
            rr = f"{float(p.get('planned_rr') or 0.0):.1f}R"
            print(f"  {ticket:<10} {sym:<18} {direction:<6} {entry:<10} {sl:<10} {tp:<10} {rr:<6}")

    print("=" * 65)
    return 0


if __name__ == "__main__":
    sys.exit(run_status())
