"""tools/operator/cmd_macro.py - Radar macroeconómico y eventos de alto impacto."""

from __future__ import annotations

import sys
from tools.operator.operator_db import get_macro_radar


def run_macro() -> int:
    radar = get_macro_radar()

    print("=" * 75)
    print("      BLACKDAEMONFX — RADAR MACROECONÓMICO Y NOTICIAS")
    print("=" * 75)
    print(f"  Estado de la Agenda:   {radar['calendar_status']}")
    print(f"  Última Actualización:  {radar['updated_at'] or 'N/A'}")
    print(f"  Divisas Afectadas:     {', '.join(radar['currencies_affected']) if radar['currencies_affected'] else 'Ninguna'}")
    print("-" * 75)
    print(f"  EVENTOS DE ALTO IMPACTO (Próximas 24-48h): {len(radar['high_impact_events'])}")

    if not radar["high_impact_events"]:
        print("  (No hay eventos de alto impacto pendientes en la agenda)")
    else:
        print(f"  {'FECHA / HORA (UTC)':<22} {'PAÍS':<6} {'EVENTO':<32} {'PREV':<8} {'EST':<8}")
        print("  " + "-" * 71)
        for e in radar["high_impact_events"]:
            dt = str(e.get("event_at") or "")[:19].replace("T", " ")
            country = str(e.get("country") or "USD")[:5]
            title = str(e.get("title") or e.get("title_original") or "")[:30]
            prev = str(e.get("previous") or "-")[:7]
            fc = str(e.get("forecast") or "-")[:7]
            print(f"  {dt:<22} {country:<6} {title:<32} {prev:<8} {fc:<8}")

    print("=" * 75)
    print("  Nota: Los índices sintéticos de Deriv tienen 0% de afectación macro.")
    print("=" * 75)
    return 0


if __name__ == "__main__":
    sys.exit(run_macro())
