"""Vigilancia de posiciones abiertas: break-even, Stop Loss y Take Profit.

Servicio puro de simulacion/seguimiento: recibe un precio desde fuera y decide
si la posicion debe pasar a break-even o cerrarse. NO consulta al broker ni
abre operaciones.

Todos los cierres que produce son ESTRUCTURALES en el sentido del proyecto:
responden a que el precio alcanzo un nivel definido en el plan (SL, TP o el
break-even), nunca a la antiguedad de una senal ni a condiciones de entrada.

Vinculaciones:
    - `position_manager.PositionManager`: estado real de las posiciones.
    - `strategy.execution.paper_trade_executor`: consumidor principal.
    - Los callbacks `on_position_updated` / `on_position_closed` permiten al
      integrador persistir o notificar cada cambio.
"""

from __future__ import annotations

from copy import deepcopy
from typing import Any, Callable, Optional

from position_manager import PositionManager, POSITION_OPEN


MONITOR_ACTION_PRICE_UPDATED = "price_updated"
MONITOR_ACTION_BREAK_EVEN_ACTIVATED = "break_even_activated"
MONITOR_ACTION_STOP_LOSS = "stop_loss"
MONITOR_ACTION_BREAK_EVEN_STOP = "break_even_stop"
MONITOR_ACTION_TAKE_PROFIT = "take_profit"


class PositionMonitoringService:
    """
    Vigila las posiciones abiertas administradas por PositionManager.

    Responsabilidades:
    - actualizar el precio actual de una posición;
    - calcular y activar Break Even al alcanzar el RR configurado;
    - detectar Stop Loss / Take Profit con el precio recibido;
    - cerrar la posición dentro de PositionManager.

    No abre operaciones ni consulta precios al broker. El precio actual debe ser
    proporcionado por la capa que integra mercado/broker.
    """

    def __init__(
        self,
        position_manager: PositionManager,
        break_even_trigger_rr: float = 1.0,
        on_position_updated: Optional[Callable[[dict[str, Any]], None]] = None,
        on_position_closed: Optional[Callable[[dict[str, Any]], None]] = None,
    ):
        """Valida las dependencias y fija el umbral de break-even.

        Args:
            position_manager: instancia real de `PositionManager`; se exige el
                tipo exacto para no operar sobre un estado inconsistente.
            break_even_trigger_rr: RR a partir del cual el SL se mueve a la
                entrada. Debe ser mayor que cero.
            on_position_updated: callback opcional en cada actualizacion.
            on_position_closed: callback opcional en cada cierre.

        Raises:
            TypeError / ValueError: ante dependencias o umbrales invalidos. Se
                valida en el constructor para que el fallo aparezca al montar
                el sistema y no con una posicion ya abierta.
        """
        if not isinstance(position_manager, PositionManager):
            raise TypeError(
                "position_manager debe ser una instancia de PositionManager."
            )

        break_even_trigger_rr = float(break_even_trigger_rr)

        if break_even_trigger_rr <= 0:
            raise ValueError(
                "break_even_trigger_rr debe ser mayor que cero."
            )

        if on_position_updated is not None and not callable(on_position_updated):
            raise TypeError("on_position_updated debe ser callable o None.")

        if on_position_closed is not None and not callable(on_position_closed):
            raise TypeError("on_position_closed debe ser callable o None.")

        self._position_manager = position_manager
        self._break_even_trigger_rr = break_even_trigger_rr
        self._on_position_updated = on_position_updated
        self._on_position_closed = on_position_closed

    @property
    def break_even_trigger_rr(self) -> float:
        """RR configurado para activar el break-even (solo lectura)."""
        return self._break_even_trigger_rr

    def monitor_position(
        self,
        ticket: str,
        current_price: float,
    ) -> dict[str, Any]:
        """Procesa un único tick/precio para una posición abierta."""

        position = self._position_manager.get_position(ticket)

        if position is None:
            raise ValueError(
                f"No existe una posición con ticket {ticket}."
            )

        if position.get("status") != POSITION_OPEN:
            raise ValueError(
                f"La posición {ticket} no está abierta."
            )

        current_price = float(current_price)
        break_even_was_active = bool(
            position.get("break_even_activated", False)
        )

        # 1. Actualizar precio y PnL flotante.
        position = self._position_manager.update_price(
            ticket=ticket,
            current_price=current_price,
        )

        # 2. Intentar activar Break Even.
        position = self._position_manager.apply_break_even(
            ticket=ticket,
            trigger_rr=self._break_even_trigger_rr,
        )

        break_even_activated_now = (
            not break_even_was_active
            and bool(position.get("break_even_activated", False))
        )

        # 3. Evaluar salida usando el SL vigente, que puede haber cambiado
        #    a la entrada en este mismo ciclo.
        exit_reason = self._resolve_exit_reason(
            position=position,
            current_price=current_price,
        )

        if exit_reason is not None:
            closed_position = self._position_manager.close_position(
                ticket=ticket,
                exit_price=current_price,
                exit_reason=exit_reason,
            )

            if self._on_position_closed is not None:
                self._on_position_closed(deepcopy(closed_position))

            return {
                "ticket": str(ticket),
                "status": closed_position["status"],
                "action": exit_reason,
                "closed": True,
                "break_even_activated": bool(
                    closed_position.get("break_even_activated", False)
                ),
                "position": deepcopy(closed_position),
            }

        action = (
            MONITOR_ACTION_BREAK_EVEN_ACTIVATED
            if break_even_activated_now
            else MONITOR_ACTION_PRICE_UPDATED
        )

        if self._on_position_updated is not None:
            self._on_position_updated(deepcopy(position))

        return {
            "ticket": str(ticket),
            "status": position["status"],
            "action": action,
            "closed": False,
            "break_even_activated": bool(
                position.get("break_even_activated", False)
            ),
            "position": deepcopy(position),
        }

    def monitor_open_positions(
        self,
        prices_by_ticket: dict[str, float],
    ) -> list[dict[str, Any]]:
        """
        Procesa las posiciones abiertas que tengan un precio disponible.

        No falla si una posición abierta no aparece en prices_by_ticket: simplemente
        no puede ser monitoreada durante ese ciclo.
        """

        if not isinstance(prices_by_ticket, dict):
            raise TypeError(
                "prices_by_ticket debe ser un diccionario."
            )

        results: list[dict[str, Any]] = []

        for position in self._position_manager.get_open_positions():
            ticket = str(position["ticket"])

            if ticket not in prices_by_ticket:
                continue

            results.append(
                self.monitor_position(
                    ticket=ticket,
                    current_price=prices_by_ticket[ticket],
                )
            )

        return results

    @staticmethod
    def _resolve_exit_reason(
        position: dict[str, Any],
        current_price: float,
    ) -> str | None:
        """Determina si el precio actual dispara un cierre, y de que tipo.

        Distingue el Stop Loss real del `break_even_stop`: cuando el SL ya se
        habia movido al precio de entrada, tocarlo no es una perdida sino una
        salida en tablas. Diferenciarlos es lo que evita contabilizar como
        derrota lo que en realidad fue un empate protegido.

        Returns:
            Una de las constantes `MONITOR_ACTION_*`, o `None` si no procede
            cerrar.

        Raises:
            ValueError: si la direccion no es BUY ni SELL.
        """
        direction = str(position["direction"]).upper()
        stop_loss = float(position["stop_loss"])
        take_profit = float(position["take_profit"])
        entry_price = float(position["filled_price"])
        break_even_activated = bool(
            position.get("break_even_activated", False)
        )

        if direction == "BUY":
            if current_price <= stop_loss:
                if break_even_activated and stop_loss == entry_price:
                    return MONITOR_ACTION_BREAK_EVEN_STOP
                return MONITOR_ACTION_STOP_LOSS

            if current_price >= take_profit:
                return MONITOR_ACTION_TAKE_PROFIT

        elif direction == "SELL":
            if current_price >= stop_loss:
                if break_even_activated and stop_loss == entry_price:
                    return MONITOR_ACTION_BREAK_EVEN_STOP
                return MONITOR_ACTION_STOP_LOSS

            if current_price <= take_profit:
                return MONITOR_ACTION_TAKE_PROFIT

        else:
            raise ValueError(
                f"Dirección inválida: {direction}"
            )

        return None
