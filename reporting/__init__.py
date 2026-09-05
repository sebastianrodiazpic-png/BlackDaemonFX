"""Paquete de informes y presentacion del bot.

Reune las cuatro salidas del sistema, todas de solo lectura sobre la base de
datos y sin capacidad de alterar decisiones de trading:

- `trade_reporting_service`: puente entre el ciclo de vida y la persistencia.
- `trade_report_exporter`: libro XLSX principal de toda la operativa.
- `trade_audit_excel_exporter`: auditoria forense "Entrada vs. Ahora" de un
  unico trade.
- `console_reporting_service`: presentacion en consola durante la ejecucion.
- `strategy_evaluation`: informe JSON offline de calibracion.

Solo se reexportan aqui los servicios de uso habitual; los exportadores se
importan por su modulo para no arrastrar `pandas` y `openpyxl` en cada import
del paquete.
"""

from reporting.trade_reporting_service import TradeReportingConfig, TradeReportingService
from reporting.console_reporting_service import ConsoleReportingConfig, ConsoleReportingService

__all__ = [
    "TradeReportingConfig",
    "TradeReportingService",
    "ConsoleReportingConfig",
    "ConsoleReportingService",
]
