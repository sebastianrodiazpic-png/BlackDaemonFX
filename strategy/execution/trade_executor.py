from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Optional


# ============================================================
# ESTADOS DE EJECUCIÓN
# ============================================================

EXECUTION_STATUS_FILLED = "FILLED"
EXECUTION_STATUS_REJECTED = "REJECTED"
EXECUTION_STATUS_CLOSED = "CLOSED"


# ============================================================
# TRADE EXECUTION REQUEST
# ============================================================

@dataclass(frozen=True)
class TradeExecutionRequest:

    symbol: str

    timeframe: str

    direction: str

    entry_time: Any

    entry_price: float

    stop_loss: float

    take_profit: float

    volume: float = 1.0

    metadata: dict[str, Any] = field(
        default_factory=dict
    )

    @classmethod
    def from_signal(
        cls,
        signal: dict[str, Any],
        volume: float = 1.0,
    ) -> "TradeExecutionRequest":

        if not isinstance(signal, dict):

            raise TypeError(
                "signal debe ser un dict"
            )

        required_fields = [

            "symbol",

            "direction",

            "entry_time",

            "entry_price",

            "stop_loss",

            "take_profit",
        ]

        missing = [

            field_name

            for field_name in required_fields

            if field_name not in signal

            or signal[field_name] is None
        ]

        if missing:

            raise ValueError(
                "Faltan campos requeridos "
                f"para ejecutar la operación: {missing}"
            )

        timeframe = (

            signal.get("timeframe")

            or signal.get("m5_timeframe")

            or "M5"
        )

        return cls(

            symbol=str(
                signal["symbol"]
            ),

            timeframe=str(
                timeframe
            ),

            direction=str(
                signal["direction"]
            ).upper(),

            entry_time=signal[
                "entry_time"
            ],

            entry_price=float(
                signal["entry_price"]
            ),

            stop_loss=float(
                signal["stop_loss"]
            ),

            take_profit=float(
                signal["take_profit"]
            ),

            volume=float(
                signal.get(
                    "volume",
                    volume,
                )
            ),

            metadata=dict(
                signal
            ),
        )


# ============================================================
# TRADE EXECUTION RESULT
# ============================================================

@dataclass
class TradeExecutionResult:

    accepted: bool

    status: str

    execution_id: str

    broker: str

    symbol: str

    timeframe: str

    direction: str

    volume: float

    requested_entry_price: float

    filled_price: Optional[float] = None

    stop_loss: Optional[float] = None

    take_profit: Optional[float] = None

    execution_time: Optional[
        datetime
    ] = None

    position_ticket: Optional[
        str
    ] = None

    reason: Optional[
        str
    ] = None

    duplicate: bool = False

    metadata: dict[str, Any] = field(
        default_factory=dict
    )

    def is_filled(self) -> bool:

        return (

            self.accepted is True

            and self.status
            == EXECUTION_STATUS_FILLED
        )


# ============================================================
# TRADE EXECUTOR ABSTRACTO
# ============================================================

class TradeExecutor(ABC):

    @abstractmethod
    def execute_trade(
        self,
        request: TradeExecutionRequest,
    ) -> TradeExecutionResult:

        """
        Ejecuta una operación.

        Implementaciones posibles:

        - PaperTradeExecutor
        - MT5TradeExecutor
        - DerivTradeExecutor
        """

        raise NotImplementedError

    @abstractmethod
    def get_position(
        self,
        position_ticket: str,
    ) -> Optional[dict[str, Any]]:

        """
        Obtiene el estado actual
        de una posición.
        """

        raise NotImplementedError

    @abstractmethod
    def close_position(
        self,
        position_ticket: str,
        exit_price: Optional[
            float
        ] = None,
        reason: str = "manual_close",
    ) -> dict[str, Any]:

        """
        Cierra una posición.
        """

        raise NotImplementedError