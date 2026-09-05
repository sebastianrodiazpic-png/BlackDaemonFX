"""Envoltura minima de sincronizacion de operaciones cerradas.

ESTADO: sin consumidores en el mapa de dependencias. La sincronizacion real la
invoca directamente `strategy.execution.live_trading_engine.sync_closed_trades`.
Se conserva como fachada delgada por si se necesita inyectar el motor en un
componente externo.
"""


class TradeMonitor:
    """Adaptador de una sola operacion sobre el motor de trading."""

    def __init__(self, engine):
        """Guarda el motor al que se delegara la sincronizacion."""
        self.engine = engine

    def sync(self):
        """Delega en `engine.sync_closed_trades()`.

        Returns:
            Lo que devuelva el motor: el numero de operaciones sincronizadas.
        """
        return self.engine.sync_closed_trades()
