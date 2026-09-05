"""Vigilancia de posiciones ya abiertas.

Complementa al motor: mientras `strategy.execution` decide entradas, este
paquete se ocupa de lo que ocurre DESPUES del fill (break-even, seguimiento,
sincronizacion de cierres).

    - `position_monitoring_service.PositionMonitoringService`: servicio activo,
      usado por `strategy.execution.paper_trade_executor`.
    - `trade_monitor.TradeMonitor`: fachada minima sin consumidores actuales.
"""

from monitoring.position_monitoring_service import (
    PositionMonitoringService,
)
