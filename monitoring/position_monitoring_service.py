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
