"""Interfaz web del bot: dashboard en tiempo real y paginas HTML.

Contenido del paquete:
    - `realtime_dashboard`: servidor HTTP y endpoints JSON.
    - `account_metrics`: agregacion de metricas de cuenta.
    - `account_page` / `trade_audit_page`: plantillas HTML.
    - `smc_visual_context`: zonas SMC en formato para graficar.

Es una capa de SOLO LECTURA: observa el estado del bot, nunca abre ni cierra
operaciones.
"""

from .realtime_dashboard import RealtimeDashboardService

__all__ = ["RealtimeDashboardService"]
