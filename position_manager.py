from copy import deepcopy


POSITION_OPEN = "OPEN"
POSITION_CLOSED = "CLOSED"


class PositionManager:

    def __init__(self):

        self._open_positions = {}
        self._closed_positions = {}

    # ============================================================
    # REGISTRAR POSICIÓN
    # ============================================================

    def register_position(self, position):

        if position is None:
            raise ValueError(
                "position no puede ser None."
            )

        if not isinstance(position, dict):
            raise TypeError(
                "position debe ser un diccionario."
            )

        required_fields = [
            "ticket",
            "symbol",
            "direction",
            "volume",
            "filled_price",
            "stop_loss",
            "take_profit",
            "status",
        ]

        missing = [
            field
            for field in required_fields
            if field not in position
        ]

        if missing:
            raise ValueError(
                f"Posición incompleta. Faltan: {missing}"
            )

        ticket = position["ticket"]

        if ticket in self._open_positions:
            raise ValueError(
                f"La posición {ticket} ya está registrada."
            )

        if ticket in self._closed_positions:
            raise ValueError(
                f"La posición {ticket} ya fue cerrada."
            )

        registered_position = deepcopy(position)

        registered_position["status"] = POSITION_OPEN

        registered_position.setdefault(
            "current_price",
            float(position["filled_price"]),
        )

        registered_position.setdefault(
            "floating_pnl_price",
            0.0,
        )

        # ----------------------------------------------------
        # BREAK EVEN
        #
        # Conservamos el stop original porque, una vez movido
        # el SL a la entrada, ya no puede utilizarse para
        # calcular el riesgo inicial de la operación.
        # ----------------------------------------------------

        registered_position.setdefault(
            "initial_stop_loss",
            float(position["stop_loss"]),
        )

        registered_position.setdefault(
            "break_even_activated",
            False,
        )

        registered_position.setdefault(
            "break_even_price",
            None,
        )

        registered_position.setdefault(
            "break_even_trigger_price",
            None,
        )

        self._open_positions[
            ticket
        ] = registered_position

        return deepcopy(
            registered_position
        )

    # ============================================================
    # OBTENER POSICIÓN
    # ============================================================

    def get_position(self, ticket):

        if ticket in self._open_positions:

            return deepcopy(
                self._open_positions[ticket]
            )

        if ticket in self._closed_positions:

            return deepcopy(
                self._closed_positions[ticket]
            )

        return None

    # ============================================================
    # OBTENER POSICIONES ABIERTAS
    # ============================================================

    def get_open_positions(self):

        return [
            deepcopy(position)
            for position in self._open_positions.values()
        ]

    # ============================================================
    # OBTENER POSICIONES CERRADAS
    # ============================================================

    def get_closed_positions(self):

        return [
            deepcopy(position)
            for position in self._closed_positions.values()
        ]

    # ============================================================
    # CONTAR POSICIONES ABIERTAS
    # ============================================================

    def open_positions_count(self):

        return len(
            self._open_positions
        )

    # ============================================================
    # CONTAR POSICIONES CERRADAS
    # ============================================================

    def closed_positions_count(self):

        return len(
            self._closed_positions
        )

    # ============================================================
    # VERIFICAR POSICIÓN ABIERTA
    # ============================================================

    def is_open(self, ticket):

        return (
            ticket
            in self._open_positions
        )

    # ============================================================
    # ACTUALIZAR PRECIO
    # ============================================================

    def update_price(
        self,
        ticket,
        current_price,
    ):

        if ticket not in self._open_positions:

            raise ValueError(
                f"No existe una posición abierta "
                f"con ticket {ticket}."
            )

        position = self._open_positions[
            ticket
        ]

        current_price = float(
            current_price
        )

        entry_price = float(
            position["filled_price"]
        )

        direction = str(
            position["direction"]
        ).upper()

        if direction == "BUY":

            floating_pnl_price = (
                current_price
                - entry_price
            )

        elif direction == "SELL":

            floating_pnl_price = (
                entry_price
                - current_price
            )

        else:

            raise ValueError(
                f"Dirección inválida: {direction}"
            )

        position["current_price"] = (
            current_price
        )

        position["floating_pnl_price"] = (
            float(floating_pnl_price)
        )

        return deepcopy(
            position
        )

    # ============================================================
    # BREAK EVEN
    # ============================================================

    def apply_break_even(
        self,
        ticket,
        trigger_rr=1.0,
    ):

        """
        Mueve el stop loss al precio de entrada cuando la posición
        alcanza la relación riesgo:beneficio indicada.

        Para una operación BUY:
            trigger = entry + riesgo_inicial * trigger_rr

        Para una operación SELL:
            trigger = entry - riesgo_inicial * trigger_rr

        El método es idempotente: una posición que ya está en
        break even no vuelve a modificar su stop loss.
        """

        if ticket not in self._open_positions:

            raise ValueError(
                f"No existe una posición abierta "
                f"con ticket {ticket}."
            )

        trigger_rr = float(
            trigger_rr
        )

        if trigger_rr <= 0:

            raise ValueError(
                "trigger_rr debe ser mayor que cero."
            )

        position = self._open_positions[
            ticket
        ]

        if position.get(
            "break_even_activated",
            False,
        ):

            return deepcopy(
                position
            )

        entry_price = float(
            position["filled_price"]
        )

        current_price = float(
            position["current_price"]
        )

        initial_stop_loss = float(
            position.get(
                "initial_stop_loss",
                position["stop_loss"],
            )
        )

        direction = str(
            position["direction"]
        ).upper()

        if direction == "BUY":

            initial_risk = (
                entry_price
                - initial_stop_loss
            )

            if initial_risk <= 0:

                raise ValueError(
                    "BUY inválido para Break Even: "
                    "initial_stop_loss debe estar bajo "
                    "filled_price."
                )

            trigger_price = (
                entry_price
                + initial_risk * trigger_rr
            )

            eligible = (
                current_price
                >= trigger_price
            )

        elif direction == "SELL":

            initial_risk = (
                initial_stop_loss
                - entry_price
            )

            if initial_risk <= 0:

                raise ValueError(
                    "SELL inválido para Break Even: "
                    "initial_stop_loss debe estar sobre "
                    "filled_price."
                )

            trigger_price = (
                entry_price
                - initial_risk * trigger_rr
            )

            eligible = (
                current_price
                <= trigger_price
            )

        else:

            raise ValueError(
                f"Dirección inválida: {direction}"
            )

        position[
            "break_even_trigger_price"
        ] = float(
            trigger_price
        )

        if not eligible:

            return deepcopy(
                position
            )

        position["stop_loss"] = (
            float(entry_price)
        )

        position[
            "break_even_activated"
        ] = True

        position[
            "break_even_price"
        ] = float(
            entry_price
        )

        return deepcopy(
            position
        )


    # ============================================================
    # CERRAR POSICIÓN
    # ============================================================

    def close_position(
        self,
        ticket,
        exit_price,
        exit_reason="manual_close",
    ):

        if ticket in self._closed_positions:

            raise ValueError(
                f"La posición {ticket} "
                f"ya fue cerrada."
            )

        if ticket not in self._open_positions:

            raise ValueError(
                f"No existe una posición abierta "
                f"con ticket {ticket}."
            )

        position = self._open_positions.pop(
            ticket
        )

        exit_price = float(
            exit_price
        )

        entry_price = float(
            position["filled_price"]
        )

        direction = str(
            position["direction"]
        ).upper()

        if direction == "BUY":

            realized_pnl_price = (
                exit_price
                - entry_price
            )

        elif direction == "SELL":

            realized_pnl_price = (
                entry_price
                - exit_price
            )

        else:

            raise ValueError(
                f"Dirección inválida: {direction}"
            )

        position["status"] = (
            POSITION_CLOSED
        )

        position["exit_price"] = (
            exit_price
        )

        position["exit_reason"] = (
            exit_reason
        )

        position["realized_pnl_price"] = (
            float(realized_pnl_price)
        )

        position["current_price"] = (
            exit_price
        )

        position["floating_pnl_price"] = (
            0.0
        )

        self._closed_positions[
            ticket
        ] = position

        return deepcopy(
            position
        )

    # ============================================================
    # LIMPIAR HISTORIAL
    # ============================================================

    def clear_closed_positions(self):

        self._closed_positions.clear()

    # ============================================================
    # LIMPIAR TODO
    # ============================================================

    def clear_all(self):

        self._open_positions.clear()

        self._closed_positions.clear()