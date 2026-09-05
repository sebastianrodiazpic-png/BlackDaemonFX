"""Registro en memoria de posiciones abiertas y cerradas, con break-even.

Es la contabilidad interna del bot sobre lo que tiene en mercado. NO habla
con ningun broker: solo mantiene el estado y calcula PnL en unidades de
precio (diferencia entre precios, sin volumen ni divisa).

Dos colecciones separadas por ticket: `_open_positions` y
`_closed_positions`. Cerrar mueve la posicion de la primera a la segunda, y
un ticket ya cerrado no puede reabrirse.

DECISION DE DISENO IMPORTANTE: todos los metodos devuelven `deepcopy` de las
posiciones. El exterior nunca recibe una referencia al estado interno, asi
que no puede corromperlo por accidente; para modificar hay que pasar
obligatoriamente por los metodos de esta clase.

Vinculaciones:
- Lo usa `strategy.execution.paper_trade_executor.PaperTradeExecutor` como
  almacen de sus posiciones simuladas.
- `monitoring.position_monitoring_service` consulta las posiciones abiertas.
- Sus datos alimentan a `trade_lifecycle_manager.TradeLifecycleManager` a
  traves del executor.
"""

from copy import deepcopy


POSITION_OPEN = "OPEN"
POSITION_CLOSED = "CLOSED"


class PositionManager:
    """Almacén de posiciones con cálculo de PnL flotante y break-even.

    Se apoya en el `ticket` como identificador unico. Las posiciones son
    dicts sueltos, no objetos, y esta clase les anade los campos de control
    (`initial_stop_loss`, `break_even_activated`, …) al registrarlas.
    """

    def __init__(self):
        """Crea el almacén vacío, sin posiciones abiertas ni cerradas."""
        self._open_positions = {}
        self._closed_positions = {}

    # ============================================================
    # REGISTRAR POSICIÓN
    # ============================================================

    def register_position(self, position):
        """Da de alta una posición recién abierta.

        Valida los campos obligatorios y que el ticket no se haya usado
        antes, ni abierto ni cerrado, para impedir duplicados.

        Guarda una COPIA PROFUNDA e inicializa los campos de control. El mas
        importante es `initial_stop_loss`: conserva el stop original porque,
        una vez movido a break-even, el `stop_loss` vigente ya no sirve para
        calcular el riesgo inicial de la operacion.

        Args:
            position: dict con `ticket`, `symbol`, `direction`, `volume`,
                `filled_price`, `stop_loss`, `take_profit` y `status`.

        Returns:
            Copia de la posicion registrada, ya con los campos de control.

        Raises:
            ValueError: si faltan campos o el ticket esta repetido.
            TypeError: si `position` no es un dict.
        """
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
        """Busca una posición por ticket, esté abierta o cerrada.

        Returns:
            Copia de la posicion, o `None` si el ticket no existe.
        """
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
        """Lista copias de todas las posiciones actualmente abiertas."""
        return [
            deepcopy(position)
            for position in self._open_positions.values()
        ]

    # ============================================================
    # OBTENER POSICIONES CERRADAS
    # ============================================================

    def get_closed_positions(self):
        """Lista copias de todas las posiciones ya cerradas."""
        return [
            deepcopy(position)
            for position in self._closed_positions.values()
        ]

    # ============================================================
    # CONTAR POSICIONES ABIERTAS
    # ============================================================

    def open_positions_count(self):
        """Número de posiciones abiertas.

        Lo consultan los limites de exposicion antes de permitir una nueva
        entrada.
        """
        return len(
            self._open_positions
        )

    # ============================================================
    # CONTAR POSICIONES CERRADAS
    # ============================================================

    def closed_positions_count(self):
        """Número de posiciones cerradas acumuladas en memoria."""
        return len(
            self._closed_positions
        )

    # ============================================================
    # VERIFICAR POSICIÓN ABIERTA
    # ============================================================

    def is_open(self, ticket):
        """Indica si el ticket corresponde a una posición viva."""
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
        """Refresca el precio actual y recalcula el PnL flotante.

        El PnL va en unidades de PRECIO, no monetarias: para BUY es
        `actual - entrada` y para SELL `entrada - actual`. Convertirlo a
        dinero es responsabilidad de quien conozca volumen y valor de punto.

        Args:
            ticket: identificador de una posicion abierta.
            current_price: ultima cotizacion.

        Returns:
            Copia de la posicion actualizada.

        Raises:
            ValueError: si el ticket no esta abierto o la direccion no es
                `BUY` ni `SELL`.
        """
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

        El riesgo inicial se calcula SIEMPRE contra `initial_stop_loss`, no
        contra el stop vigente; de otro modo, tras el primer ajuste el
        riesgo seria cero y el disparador dejaria de tener sentido.

        Requiere que `update_price` se haya llamado antes, ya que compara
        contra `current_price`.

        Aunque no se cumpla la condicion, deja anotado
        `break_even_trigger_price` para poder ver a que precio saltaria.

        Args:
            ticket: identificador de una posicion abierta.
            trigger_rr: multiplo de R que activa el break-even.

        Returns:
            Copia de la posicion, con el stop movido si procedia.

        Raises:
            ValueError: si el ticket no esta abierto, `trigger_rr` no es
                positivo, la direccion es invalida o el stop inicial esta al
                lado equivocado de la entrada.
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
        """Cierra una posición y la traslada al historial de cerradas.

        Calcula el PnL realizado en unidades de precio, anula el flotante y
        marca el estado como `CLOSED`. La operacion es irreversible: cerrar
        dos veces el mismo ticket lanza error.

        Args:
            ticket: identificador de una posicion abierta.
            exit_price: precio de salida.
            exit_reason: motivo del cierre, que se conserva tal cual para
                poder auditar despues por que se cerro cada operacion.

        Returns:
            Copia de la posicion ya cerrada.

        Raises:
            ValueError: si el ticket ya estaba cerrado, no existe abierto, o
                la direccion es invalida.
        """
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
        """Vacía el historial de cerradas, sin tocar las posiciones abiertas.

        CUIDADO: tras limpiarlo, los tickets liberados vuelven a poder
        registrarse, ya que la deteccion de duplicados se apoya en estas dos
        colecciones.
        """
        self._closed_positions.clear()

    # ============================================================
    # LIMPIAR TODO
    # ============================================================

    def clear_all(self):
        """Vacía por completo el almacén, abiertas incluidas.

        Solo para tests o reinicios: borrar posiciones vivas hace que el bot
        pierda de vista operaciones que siguen abiertas en el broker.
        """
        self._open_positions.clear()

        self._closed_positions.clear()