"""Lanzador independiente del Dashboard BlackDaemonFX en modo solo lectura.
Permite al operador visualizar en vivo el Command Center, Instrumentos,
Auditoría Forense y Telemetría en http://localhost:8765.
"""

import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from database.database import resolve_db_path
from database.repository import TradingRepository
from dashboard.realtime_dashboard import RealtimeDashboardService


def main():
    try:
        db_path = resolve_db_path()
        print(f"Conectando a base de datos canónica viva: {db_path}", flush=True)
        repo = TradingRepository(db_path=db_path)

        service = RealtimeDashboardService(
            repository=repo,
            host="127.0.0.1",
            port=8765,
        )
        service.start(live=True)
        print(f"\n========================================================", flush=True)
        print(f"🚀 Dashboard BlackDaemonFX activo en: {service.url}", flush=True)
        print(f"   • Command Center:  {service.url}/", flush=True)
        print(f"   • Instrumentos:    {service.url}/instruments", flush=True)
        print(f"   • Cuenta en vivo:  {service.url}/account", flush=True)
        print(f"========================================================\n", flush=True)

        while True:
            time.sleep(1)
    except Exception as exc:
        import traceback
        traceback.print_exc()
    except KeyboardInterrupt:
        print("\nDashboard detenido.", flush=True)


if __name__ == "__main__":
    main()
