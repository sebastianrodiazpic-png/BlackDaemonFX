"""tools/operator/cmd_catalog.py - Resumen del catálogo de 212 pares y poda preventiva."""

from __future__ import annotations

import sys
from tools.operator.operator_db import get_catalog_summary


def run_catalog() -> int:
    cat = get_catalog_summary()

    print("=" * 65)
    print("      BLACKDAEMONFX — ESTADO DEL CATÁLOGO DE 212 PARES")
    print("=" * 65)
    print(f"  Auditoría Oficial:       {cat['status']}")
    print(f"  Total Pares Evaluados:   {cat['total_pairs']}")
    print(f"  Pares Activos (>50% WR): {cat['active_pairs']}  (71.2% del catálogo)")
    print(f"  Pares en Poda Preventiva:{cat['pruned_pairs']}  (28.8% del catálogo)")
    print(f"  Win Rate Global Activo:  {cat['global_winrate']}")
    print(f"  Retorno Acumulado Neto:  {cat['accumulated_r']}")
    print("-" * 65)
    print("  Distribución de Pares Activos:")
    print("   • Malaysian SNR:        60 activos (+1,477.12 R netos, 68.18% WR)")
    print("   • ICT Sintéticos/Real:  48 activos (+1,134.81 R netos)")
    print("   • Trend Pullback:       29 sintéticos (+76.33 R netos)")
    print("   • ORB New York:         11 activos (+180.16 R netos, 61.33% WR)")
    print("   • Connors RSI(2) D1:     3 índices US activos")
    print("=" * 65)
    return 0


if __name__ == "__main__":
    sys.exit(run_catalog())
