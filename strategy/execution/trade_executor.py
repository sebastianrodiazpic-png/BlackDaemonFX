"""Contrato abstracto de ejecución de operaciones y sus tipos de datos.

Define la FRONTERA entre la logica del bot y el mundo exterior. Todo lo que
hay por encima (lifecycle manager, motor en vivo) habla solo este lenguaje, y
cada broker concreto implementa `TradeExecutor` a su manera. Gracias a eso se
puede pasar de papel a real sin tocar la estrategia.

Tres piezas:
- `TradeExecutionRequest`: la peticion, INMUTABLE (`frozen=True`).
- `TradeExecutionResult`: la respuesta, mutable y con toda la informacion de
  lo que el broker hizo realmente.
- `TradeExecutor`: la interfaz que hay que implementar.

Vinculaciones:
- `strategy.execution.paper_trade_executor.PaperTradeExecutor` es la
  implementacion de papel.
- Los ejecutores reales viven en `brokers/`.
- `trade_lifecycle_manager.TradeLifecycleManager` es el consumidor principal.
"""

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
    """Petición inmutable de apertura de una operación.

    Es INMUTABLE a proposito: una vez formulada la orden, nadie puede
    alterarla por el camino. Lo que el broker devuelva puede diferir, pero
    quedara reflejado en el `TradeExecutionResult`, no aqui.
    """

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
        """Construye la petición a partir del dict de señal de una estrategia.

        Detalles a tener en cuenta:
        - Los campos obligatorios se rechazan tanto si faltan como si valen
          `None`, porque un stop nulo seria mucho peor que un stop ausente.
        - El timeframe se busca en `timeframe`, luego `m5_timeframe`, y por
          ultimo cae en `M5`.
        - La direccion se normaliza a mayusculas.
        - El volumen de la senal tiene prioridad sobre el argumento.
        - `metadata` recibe una copia COMPLETA de la senal, de modo que toda
          la informacion del analisis viaja con la orden y puede auditarse
          despues.

        Raises:
            TypeError: si `signal` no es un dict.
            ValueError: si falta algun campo obligatorio.
        """
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
    """Respuesta del broker a una petición de ejecución.

    Distingue tres nociones que conviene no confundir:
    - `accepted`: el broker admitio la orden.
    - `status`: `FILLED`, `REJECTED` o `CLOSED`.
    - `duplicate`: la orden se reconocio como repetida y no se abrio una
      posicion nueva. Es la defensa contra doble entrada por reintentos.

    `requested_entry_price` frente a `filled_price` permite medir el
    deslizamiento real de cada ejecucion.
    """

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
        """Indica si la orden se llenó de verdad.

        Exige AMBAS condiciones: aceptada y con estado `FILLED`. Aceptada
        pero sin llenar no es una posicion abierta.
        """
        return (

            self.accepted is True

            and self.status
            == EXECUTION_STATUS_FILLED
        )


# ============================================================
# TRADE EXECUTOR ABSTRACTO
# ============================================================

class TradeExecutor(ABC):
    """Interfaz que debe implementar todo ejecutor de operaciones.

    Los tres metodos abstractos son el minimo imprescindible. Ademas, quien
    quiera soportar monitoreo continuo debe ofrecer `monitor_position`, que
    NO es abstracto pero si lo comprueba
    `trade_lifecycle_manager.TradeLifecycleManager.monitor_execution` antes
    de usarlo.
    """

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

        Debe devolver SIEMPRE un `TradeExecutionResult`, tambien cuando la
        orden se rechaza: el rechazo es una respuesta valida, no un error.
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

        Devuelve `None` si el ticket no existe. Debe funcionar tanto con
        posiciones abiertas como cerradas, ya que el lifecycle manager lo
        consulta despues de detectar un cierre para leer el precio y el
        motivo de salida.
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

        Debe devolver un dict con al menos `closed` (bool), y cuando el
        cierre se confirme tambien `exit_price`, `reason` y
        `realized_pnl_price`.

        La clave `closed` es CRITICA: el lifecycle manager se niega a dar por
        cerrada la operacion si no viene a `True`, para no perder de vista
        una posicion que siga viva en el broker.
        """

        raise NotImplementedError