from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Optional

from monitoring.position_monitoring_service import PositionMonitoringService
from position_manager import POSITION_OPEN, PositionManager

from strategy.execution.trade_executor import (
    EXECUTION_STATUS_CLOSED,
    EXECUTION_STATUS_FILLED,
    TradeExecutionRequest,
    TradeExecutionResult,
    TradeExecutor,
)


class PaperTradeExecutor(
    TradeExecutor
):

    """
    Ejecuta operaciones virtuales.

    No envía órdenes al broker.

    Características:

    - valida BUY / SELL
    - valida SL / TP
    - valida volumen
    - genera tickets virtuales
    - evita duplicados
    - mantiene posiciones virtuales
    - permite cierre manual virtual
    """

    BROKER_NAME = "PAPER"

    def __init__(
        self,
        position_manager: Optional[PositionManager] = None,
        break_even_trigger_rr: float = 1.0,
    ):

        if position_manager is not None and not isinstance(position_manager, PositionManager):
            raise TypeError("position_manager debe ser PositionManager o None")

        self._position_manager = position_manager or PositionManager()
        self._position_monitoring_service = PositionMonitoringService(
            position_manager=self._position_manager,
            break_even_trigger_rr=break_even_trigger_rr,
            on_position_updated=self._sync_position_update_from_manager,
            on_position_closed=self._sync_position_close_from_manager,
        )

        self._positions: dict[
            str,
            dict[str, Any]
        ] = {}

        self._execution_results: dict[
            str,
            TradeExecutionResult
        ] = {}

        self._execution_keys: dict[
            str,
            str
        ] = {}

        self._counter = 0

    # ========================================================
    # EJECUTAR TRADE
    # ========================================================

    def execute_trade(
        self,
        request: TradeExecutionRequest,
    ) -> TradeExecutionResult:

        if not isinstance(
            request,
            TradeExecutionRequest,
        ):

            raise TypeError(
                "request debe ser "
                "TradeExecutionRequest"
            )

        self._validate_request(
            request
        )

        execution_key = (
            self._build_execution_key(
                request
            )
        )

        # ----------------------------------------------------
        # IDEMPOTENCIA
        #
        # La misma señal no debe abrir
        # una segunda operación.
        # ----------------------------------------------------

        existing_ticket = (
            self._execution_keys.get(
                execution_key
            )
        )

        if existing_ticket is not None:

            existing = (
                self._execution_results[
                    existing_ticket
                ]
            )

            return TradeExecutionResult(

                accepted=existing.accepted,

                status=existing.status,

                execution_id=(
                    existing.execution_id
                ),

                broker=existing.broker,

                symbol=existing.symbol,

                timeframe=existing.timeframe,

                direction=existing.direction,

                volume=existing.volume,

                requested_entry_price=(
                    existing.requested_entry_price
                ),

                filled_price=(
                    existing.filled_price
                ),

                stop_loss=existing.stop_loss,

                take_profit=(
                    existing.take_profit
                ),

                execution_time=(
                    existing.execution_time
                ),

                position_ticket=(
                    existing.position_ticket
                ),

                reason=(
                    "duplicate_execution_key"
                ),

                duplicate=True,

                metadata=dict(
                    existing.metadata
                ),
            )

        # ----------------------------------------------------
        # NUEVO TICKET
        # ----------------------------------------------------

        self._counter += 1

        ticket = (
            f"PAPER-{self._counter:06d}"
        )

        execution_time = (
            datetime.now(
                timezone.utc
            )
        )

        # ----------------------------------------------------
        # PAPER FILL
        #
        # En esta primera versión,
        # la operación se llena al precio solicitado.
        # ----------------------------------------------------

        result = TradeExecutionResult(

            accepted=True,

            status=(
                EXECUTION_STATUS_FILLED
            ),

            execution_id=ticket,

            broker=self.BROKER_NAME,

            symbol=request.symbol,

            timeframe=request.timeframe,

            direction=request.direction,

            volume=request.volume,

            requested_entry_price=(
                request.entry_price
            ),

            filled_price=(
                request.entry_price
            ),

            stop_loss=request.stop_loss,

            take_profit=(
                request.take_profit
            ),

            execution_time=execution_time,

            position_ticket=ticket,

            reason="paper_filled",

            duplicate=False,

            metadata=dict(
                request.metadata
            ),
        )

        self._execution_results[
            ticket
        ] = result

        self._execution_keys[
            execution_key
        ] = ticket

        self._positions[
            ticket
        ] = {

            "position_ticket": ticket,

            "execution_id": ticket,

            "broker": (
                self.BROKER_NAME
            ),

            "status": (
                EXECUTION_STATUS_FILLED
            ),

            "symbol": (
                request.symbol
            ),

            "timeframe": (
                request.timeframe
            ),

            "direction": (
                request.direction
            ),

            "volume": (
                request.volume
            ),

            "entry_time": (
                request.entry_time
            ),

            "entry_price": (
                request.entry_price
            ),

            "stop_loss": (
                request.stop_loss
            ),

            "take_profit": (
                request.take_profit
            ),

            "filled_price": (
                request.entry_price
            ),

            "execution_time": (
                execution_time
            ),

            "exit_time": None,

            "exit_price": None,

            "exit_reason": None,
        }

        self._position_manager.register_position(
            self._to_managed_position(self._positions[ticket])
        )

        return result

    # ========================================================
    # OBTENER POSICIÓN
    # ========================================================

    def get_position(
        self,
        position_ticket: str,
    ) -> Optional[dict[str, Any]]:

        position = (
            self._positions.get(
                str(position_ticket)
            )
        )

        if position is None:

            return None

        managed_position = self._position_manager.get_position(str(position_ticket))

        if managed_position is not None:
            return self._merge_paper_and_managed_position(
                paper_position=position,
                managed_position=managed_position,
            )

        return dict(position)

    # ========================================================
    # CERRAR POSICIÓN
    # ========================================================

    def close_position(
        self,
        position_ticket: str,
        exit_price: Optional[
            float
        ] = None,
        reason: str = "manual_close",
    ) -> dict[str, Any]:

        ticket = str(
            position_ticket
        )

        position = (
            self._positions.get(
                ticket
            )
        )

        if position is None:

            raise ValueError(
                "No existe la posición: "
                f"{ticket}"
            )

        if position["status"] == (
            EXECUTION_STATUS_CLOSED
        ):

            raise RuntimeError(
                "La posición ya está cerrada: "
                f"{ticket}"
            )

        if exit_price is None:

            exit_price = (
                position["filled_price"]
            )

        position["status"] = (
            EXECUTION_STATUS_CLOSED
        )

        position["exit_price"] = float(
            exit_price
        )

        position["exit_reason"] = str(
            reason
        )

        position["exit_time"] = (
            datetime.now(
                timezone.utc
            )
        )

        if self._position_manager.is_open(ticket):
            managed_position = self._position_manager.close_position(
                ticket=ticket,
                exit_price=float(exit_price),
                exit_reason=str(reason),
            )
            self._sync_position_close_from_manager(managed_position)

        return self.get_position(ticket)

    # ========================================================
    # MONITOREAR POSICIÓN
    # ========================================================

    @property
    def position_manager(self) -> PositionManager:
        return self._position_manager

    @property
    def position_monitoring_service(self) -> PositionMonitoringService:
        return self._position_monitoring_service

    def monitor_position(
        self,
        position_ticket: str,
        current_price: float,
    ) -> dict[str, Any]:
        return self._position_monitoring_service.monitor_position(
            ticket=str(position_ticket),
            current_price=float(current_price),
        )

    def monitor_open_positions(
        self,
        prices_by_ticket: dict[str, float],
    ) -> list[dict[str, Any]]:
        return self._position_monitoring_service.monitor_open_positions(
            prices_by_ticket=prices_by_ticket,
        )

    # ========================================================
    # SINCRONIZACIÓN CON POSITION MANAGER
    # ========================================================

    @staticmethod
    def _to_managed_position(position: dict[str, Any]) -> dict[str, Any]:
        return {
            "ticket": str(position["position_ticket"]),
            "symbol": position["symbol"],
            "direction": position["direction"],
            "volume": position["volume"],
            "filled_price": position["filled_price"],
            "stop_loss": position["stop_loss"],
            "take_profit": position["take_profit"],
            "status": POSITION_OPEN,
        }

    def _sync_position_update_from_manager(
        self,
        managed_position: dict[str, Any],
    ) -> None:
        ticket = str(managed_position["ticket"])
        position = self._positions.get(ticket)
        if position is None:
            return

        for field in (
            "current_price",
            "floating_pnl_price",
            "stop_loss",
            "take_profit",
            "break_even_activated",
            "break_even_price",
            "break_even_trigger_price",
            "initial_stop_loss",
        ):
            if field in managed_position:
                position[field] = managed_position[field]

    def _sync_position_close_from_manager(
        self,
        managed_position: dict[str, Any],
    ) -> None:
        ticket = str(managed_position["ticket"])
        position = self._positions.get(ticket)
        if position is None:
            return

        self._sync_position_update_from_manager(managed_position)
        position["status"] = EXECUTION_STATUS_CLOSED
        position["exit_price"] = managed_position.get("exit_price")
        position["exit_reason"] = managed_position.get("exit_reason")
        position["realized_pnl_price"] = managed_position.get("realized_pnl_price")
        position["current_price"] = managed_position.get("current_price")
        position["floating_pnl_price"] = managed_position.get("floating_pnl_price")
        if position.get("exit_time") is None:
            position["exit_time"] = datetime.now(timezone.utc)

    @staticmethod
    def _merge_paper_and_managed_position(
        paper_position: dict[str, Any],
        managed_position: dict[str, Any],
    ) -> dict[str, Any]:
        merged = dict(paper_position)
        merged.update({
            "managed_status": managed_position.get("status"),
            "current_price": managed_position.get("current_price"),
            "floating_pnl_price": managed_position.get("floating_pnl_price"),
            "realized_pnl_price": managed_position.get("realized_pnl_price"),
            "stop_loss": managed_position.get("stop_loss", paper_position.get("stop_loss")),
            "take_profit": managed_position.get("take_profit", paper_position.get("take_profit")),
            "break_even_activated": managed_position.get("break_even_activated", False),
            "break_even_price": managed_position.get("break_even_price"),
            "break_even_trigger_price": managed_position.get("break_even_trigger_price"),
            "initial_stop_loss": managed_position.get("initial_stop_loss"),
        })
        if managed_position.get("exit_price") is not None:
            merged["exit_price"] = managed_position.get("exit_price")
        if managed_position.get("exit_reason") is not None:
            merged["exit_reason"] = managed_position.get("exit_reason")
        return merged

    # ========================================================
    # LISTAR POSICIONES
    # ========================================================

    def get_positions(
        self,
    ) -> list[dict[str, Any]]:

        return [

            dict(position)

            for position in
            self._positions.values()
        ]

    # ========================================================
    # LISTAR POSICIONES ABIERTAS
    # ========================================================

    def get_open_positions(
        self,
    ) -> list[dict[str, Any]]:

        return [

            dict(position)

            for position in
            self._positions.values()

            if position["status"]
            == EXECUTION_STATUS_FILLED
        ]

    # ========================================================
    # VALIDAR REQUEST
    # ========================================================

    @staticmethod
    def _validate_request(
        request: TradeExecutionRequest,
    ) -> None:

        direction = (
            str(
                request.direction
            ).upper()
        )

        if direction not in {
            "BUY",
            "SELL",
        }:

            raise ValueError(
                "direction debe ser BUY o SELL"
            )

        if not request.symbol:

            raise ValueError(
                "symbol no puede estar vacío"
            )

        if not request.timeframe:

            raise ValueError(
                "timeframe no puede estar vacío"
            )

        if request.volume <= 0:

            raise ValueError(
                "volume debe ser mayor que cero"
            )

        entry = float(
            request.entry_price
        )

        stop = float(
            request.stop_loss
        )

        target = float(
            request.take_profit
        )

        # ----------------------------------------------------
        # BUY
        # ----------------------------------------------------

        if direction == "BUY":

            if not (
                stop < entry < target
            ):

                raise ValueError(
                    "BUY inválido: "
                    "debe cumplirse "
                    "stop_loss < entry_price "
                    "< take_profit"
                )

        # ----------------------------------------------------
        # SELL
        # ----------------------------------------------------

        if direction == "SELL":

            if not (
                target < entry < stop
            ):

                raise ValueError(
                    "SELL inválido: "
                    "debe cumplirse "
                    "take_profit < entry_price "
                    "< stop_loss"
                )

    # ========================================================
    # CREAR EXECUTION KEY
    # ========================================================

    @staticmethod
    def _build_execution_key(
        request: TradeExecutionRequest,
    ) -> str:

        return ":".join([

            str(
                request.symbol
            ),

            str(
                request.timeframe
            ),

            str(
                request.direction
            ).upper(),

            str(
                request.entry_time
            ),

            str(
                request.entry_price
            ),

            str(
                request.stop_loss
            ),

            str(
                request.take_profit
            ),
        ])