from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Callable, Optional

from strategy.execution.trade_executor import (
    EXECUTION_STATUS_FILLED,
    TradeExecutionRequest,
    TradeExecutionResult,
    TradeExecutor,
)

import pandas as pd


# ============================================================
# ESTADOS DEL CICLO DE VIDA
# ============================================================

STATE_READY_TO_ENTER = "READY_TO_ENTER"
STATE_EXECUTION = "EXECUTION"

STATE_WIN = "WIN"
STATE_LOSS = "LOSS"
STATE_AMBIGUOUS = "AMBIGUOUS"
STATE_EXPIRED = "EXPIRED"
STATE_BREAK_EVEN = "BREAK_EVEN"
STATE_CLOSED = "CLOSED"

FINAL_STATES = {
    STATE_WIN,
    STATE_LOSS,
    STATE_AMBIGUOUS,
    STATE_EXPIRED,
    STATE_BREAK_EVEN,
    STATE_CLOSED,
}


# ============================================================
# RESULTADOS DEL TRADE SIMULATOR
# ============================================================

SIMULATION_WIN = "win"
SIMULATION_LOSS = "loss"
SIMULATION_AMBIGUOUS = "ambiguous"
SIMULATION_EXPIRED = "expired"


# ============================================================
# TRADE LIFECYCLE
# ============================================================

@dataclass
class TradeLifecycle:

    symbol: str

    timeframe: str

    direction: str

    entry_time: Any

    entry_price: float

    stop_loss: float

    take_profit: float

    risk_reward_ratio: Optional[float] = None

    state: str = STATE_READY_TO_ENTER

    result: Optional[str] = None

    exit_time: Optional[Any] = None

    exit_price: Optional[float] = None

    exit_reason: Optional[str] = None

    bars_held: Optional[int] = None

    pnl_price: float = 0.0

    position_ticket: Optional[str] = None

    execution_id: Optional[str] = None

    execution_status: Optional[str] = None

    execution_time: Optional[Any] = None

    metadata: dict[str, Any] = field(
        default_factory=dict
    )

    def is_final(self) -> bool:

        return self.state in FINAL_STATES

    def to_dict(self) -> dict[str, Any]:

        return {
            "symbol": self.symbol,

            "timeframe": self.timeframe,

            "direction": self.direction,

            "entry_time": self.entry_time,

            "entry_price": self.entry_price,

            "stop_loss": self.stop_loss,

            "take_profit": self.take_profit,

            "risk_reward_ratio": (
                self.risk_reward_ratio
            ),

            "state": self.state,

            "result": self.result,

            "exit_time": self.exit_time,

            "exit_price": self.exit_price,

            "exit_reason": self.exit_reason,

            "bars_held": self.bars_held,

            "pnl_price": self.pnl_price,

            "position_ticket": self.position_ticket,

            "execution_id": self.execution_id,

            "execution_status": self.execution_status,

            "execution_time": self.execution_time,

            "metadata": self.metadata,
        }


# ============================================================
# TRADE LIFECYCLE MANAGER
# ============================================================

class TradeLifecycleManager:

    def __init__(
        self,
        trade_simulator: Optional[Callable[..., dict[str, Any]]] = None,
        trade_executor: Optional[TradeExecutor] = None,
        reporting_service: Optional[Any] = None,
    ):

        if trade_simulator is not None and not callable(trade_simulator):
            raise TypeError("trade_simulator debe ser una función callable o None")

        if trade_executor is not None and not isinstance(trade_executor, TradeExecutor):
            raise TypeError("trade_executor debe implementar TradeExecutor")

        if trade_simulator is None and trade_executor is None:
            raise ValueError("Debe proporcionar trade_simulator o trade_executor")

        if reporting_service is not None and not callable(
            getattr(reporting_service, "on_lifecycle_event", None)
        ):
            raise TypeError(
                "reporting_service debe implementar on_lifecycle_event"
            )

        self.trade_simulator = trade_simulator
        self.trade_executor = trade_executor
        self.reporting_service = reporting_service

        self.lifecycle_history: list[TradeLifecycle] = []
        self._active_lifecycles: dict[str, TradeLifecycle] = {}

    # ========================================================
    # CREAR LIFECYCLE DESDE READY_TO_ENTER
    # ========================================================

    def create_from_signal(
        self,
        signal: dict[str, Any],
    ) -> TradeLifecycle:

        self._validate_signal(signal)

        lifecycle = TradeLifecycle(

            symbol=signal["symbol"],

            timeframe=self._get_timeframe(signal),

            direction=signal["direction"],

            entry_time=signal["entry_time"],

            entry_price=float(
                signal["entry_price"]
            ),

            stop_loss=float(
                signal["stop_loss"]
            ),

            take_profit=float(
                signal["take_profit"]
            ),

            risk_reward_ratio=signal.get(
                "risk_reward_ratio"
            ),

            state=STATE_READY_TO_ENTER,

            metadata={
                "source_action": signal.get(
                    "action"
                ),
            },
        )

        return lifecycle

    # ========================================================
    # EJECUTAR LIFECYCLE
    # ========================================================

    def execute(
        self,
        lifecycle: TradeLifecycle,
        candles: pd.DataFrame,
        max_bars: int = 500,
    ) -> TradeLifecycle:

        if lifecycle.is_final():

            raise RuntimeError(
                "No se puede ejecutar un lifecycle "
                "que ya está finalizado"
            )

        if self.trade_simulator is None:
            raise RuntimeError("TradeLifecycleManager no tiene trade_simulator configurado")

        self._validate_candles(candles)

        # ----------------------------------------------------
        # TRANSICION
        #
        # READY_TO_ENTER -> EXECUTION
        # ----------------------------------------------------

        lifecycle.state = STATE_EXECUTION

        # ----------------------------------------------------
        # CREAR TRADE PARA EL SIMULADOR
        # ----------------------------------------------------

        trade = pd.Series({

            "entry_time": lifecycle.entry_time,

            "entry_price": lifecycle.entry_price,

            "stop_loss": lifecycle.stop_loss,

            "take_profit": lifecycle.take_profit,

            "trade_type": (
                "long"
                if lifecycle.direction == "BUY"
                else "short"
            ),
        })

        # ----------------------------------------------------
        # EJECUTAR TRADE SIMULATOR
        # ----------------------------------------------------

        simulation = self.trade_simulator(

            df=candles,

            trade=trade,

            max_bars=max_bars,
        )

        if simulation is None:

            raise RuntimeError(
                "trade_simulator devolvió None"
            )

        if not isinstance(simulation, dict):

            raise TypeError(
                "trade_simulator debe devolver un dict"
            )

        if "result" not in simulation:

            raise ValueError(
                "El resultado del trade_simulator "
                "no contiene la clave 'result'"
            )

        # ----------------------------------------------------
        # APLICAR RESULTADO
        # ----------------------------------------------------

        self._apply_simulation_result(

            lifecycle=lifecycle,

            simulation=simulation,
        )

        # ----------------------------------------------------
        # GUARDAR HISTORIAL
        # ----------------------------------------------------

        self._record_final_lifecycle(lifecycle)
        self._notify_reporting(
            event="LIFECYCLE_FINALIZED",
            lifecycle=lifecycle,
        )

        return lifecycle

    # ========================================================
    # CREAR + EJECUTAR
    # ========================================================

    def process_signal(
        self,
        signal: dict[str, Any],
        candles: pd.DataFrame,
        max_bars: int = 500,
    ) -> TradeLifecycle:

        lifecycle = self.create_from_signal(
            signal=signal
        )

        return self.execute(

            lifecycle=lifecycle,

            candles=candles,

            max_bars=max_bars,
        )

    # ========================================================
    # EJECUTAR LIFECYCLE EN EXECUTOR REAL / PAPER
    # ========================================================

    def execute_with_executor(
        self,
        lifecycle: TradeLifecycle,
        volume: float = 1.0,
        trade_executor: Optional[TradeExecutor] = None,
    ) -> TradeLifecycle:
        if lifecycle.is_final():
            raise RuntimeError("No se puede ejecutar un lifecycle que ya está finalizado")

        executor = trade_executor or self.trade_executor
        if executor is None:
            raise RuntimeError("No hay trade_executor configurado")
        if not isinstance(executor, TradeExecutor):
            raise TypeError("trade_executor debe implementar TradeExecutor")

        if lifecycle.state == STATE_EXECUTION and lifecycle.position_ticket:
            raise RuntimeError("El lifecycle ya tiene una operación activa")

        request = TradeExecutionRequest(
            symbol=lifecycle.symbol,
            timeframe=lifecycle.timeframe,
            direction=lifecycle.direction,
            entry_time=lifecycle.entry_time,
            entry_price=lifecycle.entry_price,
            stop_loss=lifecycle.stop_loss,
            take_profit=lifecycle.take_profit,
            volume=float(volume),
            metadata={
                **dict(lifecycle.metadata),
                "lifecycle_symbol": lifecycle.symbol,
                "lifecycle_entry_time": str(lifecycle.entry_time),
            },
        )

        result = executor.execute_trade(request)
        if not isinstance(result, TradeExecutionResult):
            raise TypeError("trade_executor debe devolver TradeExecutionResult")

        lifecycle.execution_status = result.status
        lifecycle.execution_id = result.execution_id
        lifecycle.metadata["volume"] = float(volume)
        lifecycle.execution_time = result.execution_time
        lifecycle.position_ticket = result.position_ticket
        lifecycle.metadata["execution_broker"] = result.broker
        lifecycle.metadata["execution_reason"] = result.reason
        lifecycle.metadata["execution_duplicate"] = bool(result.duplicate)

        if not result.is_filled():
            lifecycle.metadata["execution_accepted"] = bool(result.accepted)
            self._notify_reporting(
                event="EXECUTION_REJECTED",
                lifecycle=lifecycle,
                volume=volume,
            )
            return lifecycle

        lifecycle.state = STATE_EXECUTION
        lifecycle.entry_price = float(result.filled_price or lifecycle.entry_price)
        lifecycle.stop_loss = float(result.stop_loss or lifecycle.stop_loss)
        lifecycle.take_profit = float(result.take_profit or lifecycle.take_profit)

        if not lifecycle.position_ticket:
            raise RuntimeError("El executor llenó la operación sin position_ticket")

        self._active_lifecycles[str(lifecycle.position_ticket)] = lifecycle
        self._notify_reporting(
            event="EXECUTION_FILLED",
            lifecycle=lifecycle,
            volume=volume,
        )
        return lifecycle

    def process_signal_with_executor(
        self,
        signal: dict[str, Any],
        volume: float = 1.0,
        trade_executor: Optional[TradeExecutor] = None,
    ) -> TradeLifecycle:
        lifecycle = self.create_from_signal(signal)
        return self.execute_with_executor(
            lifecycle=lifecycle,
            volume=volume,
            trade_executor=trade_executor,
        )

    # ========================================================
    # MONITOREAR OPERACIÓN ACTIVA
    # ========================================================

    def close_execution(
        self,
        lifecycle: TradeLifecycle,
        trade_executor: Optional[TradeExecutor] = None,
        reason: str = "manual_close",
    ) -> dict[str, Any]:
        """Cierra una posición activa mediante el executor y finaliza el lifecycle."""
        if lifecycle.is_final():
            raise RuntimeError("No se puede cerrar un lifecycle ya finalizado")
        if lifecycle.state != STATE_EXECUTION or not lifecycle.position_ticket:
            raise RuntimeError("El lifecycle no tiene una posición activa para cerrar")

        executor = trade_executor or self.trade_executor
        if executor is None:
            raise RuntimeError("No hay trade_executor configurado")

        close_result = executor.close_position(
            position_ticket=str(lifecycle.position_ticket),
            reason=reason,
        )
        if not isinstance(close_result, dict) or not close_result.get("closed", False):
            raise RuntimeError("El executor no confirmó el cierre de la posición")

        lifecycle.exit_time = datetime.now(timezone.utc)
        lifecycle.exit_price = close_result.get("exit_price")
        lifecycle.exit_reason = str(close_result.get("reason") or reason)
        lifecycle.pnl_price = float(close_result.get("realized_pnl_price", 0.0) or 0.0)
        lifecycle.result = self._result_from_exit_reason(lifecycle.exit_reason)
        lifecycle.state = self._state_from_exit_reason(lifecycle.exit_reason)
        lifecycle.execution_status = "CLOSED"
        self._active_lifecycles.pop(str(lifecycle.position_ticket), None)
        self._record_final_lifecycle(lifecycle)
        self._notify_reporting(
            event="LIFECYCLE_FINALIZED",
            lifecycle=lifecycle,
        )
        return close_result

    def monitor_execution(
        self,
        lifecycle: TradeLifecycle,
        current_price: float,
        trade_executor: Optional[TradeExecutor] = None,
    ) -> dict[str, Any]:
        if lifecycle.is_final():
            raise RuntimeError("No se puede monitorear un lifecycle finalizado")
        if lifecycle.state != STATE_EXECUTION or not lifecycle.position_ticket:
            raise RuntimeError("El lifecycle no tiene una operación activa para monitorear")

        executor = trade_executor or self.trade_executor
        if executor is None:
            raise RuntimeError("No hay trade_executor configurado")
        monitor = getattr(executor, "monitor_position", None)
        if not callable(monitor):
            raise TypeError("El trade_executor no soporta monitor_position")

        monitor_result = monitor(
            position_ticket=str(lifecycle.position_ticket),
            current_price=float(current_price),
        )
        if not isinstance(monitor_result, dict):
            raise TypeError("monitor_position debe devolver un dict")

        position = monitor_result.get("position") or executor.get_position(str(lifecycle.position_ticket))
        if position:
            lifecycle.stop_loss = float(position.get("stop_loss", lifecycle.stop_loss))
            lifecycle.take_profit = float(position.get("take_profit", lifecycle.take_profit))
            lifecycle.metadata["break_even_activated"] = bool(position.get("break_even_activated", False))
            lifecycle.metadata["current_price"] = position.get("current_price", current_price)
            lifecycle.metadata["floating_pnl_price"] = position.get("floating_pnl_price")

        lifecycle.execution_status = monitor_result.get("status", lifecycle.execution_status)

        if not monitor_result.get("closed", False):
            self._notify_reporting(
                event="POSITION_UPDATED",
                lifecycle=lifecycle,
            )
            return monitor_result

        exit_price = None if position is None else position.get("exit_price")
        exit_reason = None if position is None else position.get("exit_reason")
        lifecycle.exit_time = datetime.now(timezone.utc)
        lifecycle.exit_price = None if exit_price is None else float(exit_price)
        lifecycle.exit_reason = str(exit_reason or monitor_result.get("action"))
        lifecycle.bars_held = lifecycle.bars_held
        lifecycle.pnl_price = float((position or {}).get("realized_pnl_price", 0.0) or 0.0)
        lifecycle.result = self._result_from_exit_reason(lifecycle.exit_reason)
        lifecycle.state = self._state_from_exit_reason(lifecycle.exit_reason)
        self._active_lifecycles.pop(str(lifecycle.position_ticket), None)
        self._record_final_lifecycle(lifecycle)
        self._notify_reporting(
            event="LIFECYCLE_FINALIZED",
            lifecycle=lifecycle,
        )
        return monitor_result

    def monitor_open_executions(
        self,
        prices_by_ticket: dict[str, float],
        trade_executor: Optional[TradeExecutor] = None,
    ) -> list[dict[str, Any]]:
        if not isinstance(prices_by_ticket, dict):
            raise TypeError("prices_by_ticket debe ser un dict")
        results = []
        for ticket, lifecycle in list(self._active_lifecycles.items()):
            if ticket not in prices_by_ticket:
                continue
            results.append(self.monitor_execution(
                lifecycle=lifecycle,
                current_price=float(prices_by_ticket[ticket]),
                trade_executor=trade_executor,
            ))
        return results

    def get_active_lifecycle(self, position_ticket: str) -> Optional[TradeLifecycle]:
        return self._active_lifecycles.get(str(position_ticket))

    def get_active_lifecycles(self) -> list[TradeLifecycle]:
        return list(self._active_lifecycles.values())

    def _notify_reporting(
        self,
        event: str,
        lifecycle: TradeLifecycle,
        volume: Optional[float] = None,
    ) -> Any:
        """
        Publica cambios relevantes del lifecycle hacia el servicio de reporting.

        El manager sigue siendo dueño de las transiciones de estado; el servicio
        externo solamente persiste y exporta el resultado.
        """
        if self.reporting_service is None:
            return None

        return self.reporting_service.on_lifecycle_event(
            event=event,
            lifecycle=lifecycle,
            volume=volume,
        )

    def _record_final_lifecycle(self, lifecycle: TradeLifecycle) -> None:
        if lifecycle.is_final() and not any(item is lifecycle for item in self.lifecycle_history):
            self.lifecycle_history.append(lifecycle)

    @staticmethod
    def _result_from_exit_reason(exit_reason: str) -> str:
        mapping = {
            "take_profit": "win",
            "stop_loss": "loss",
            "break_even_stop": "break_even",
            "manual_close": "closed",
        }
        return mapping.get(str(exit_reason), str(exit_reason))

    @staticmethod
    def _state_from_exit_reason(exit_reason: str) -> str:
        mapping = {
            "take_profit": STATE_WIN,
            "stop_loss": STATE_LOSS,
            "break_even_stop": STATE_BREAK_EVEN,
            "manual_close": STATE_CLOSED,
        }
        return mapping.get(str(exit_reason), STATE_CLOSED)

    # ========================================================
    # APLICAR RESULTADO DEL SIMULADOR
    # ========================================================

    def _apply_simulation_result(
        self,
        lifecycle: TradeLifecycle,
        simulation: dict[str, Any],
    ) -> None:

        result = simulation["result"]

        lifecycle.result = result

        lifecycle.exit_time = simulation.get(
            "exit_time"
        )

        lifecycle.exit_price = simulation.get(
            "exit_price"
        )

        lifecycle.exit_reason = simulation.get(
            "exit_reason"
        )

        lifecycle.bars_held = simulation.get(
            "bars_held"
        )

        lifecycle.pnl_price = float(
            simulation.get(
                "pnl_price",
                0.0,
            )
        )

        # ----------------------------------------------------
        # WIN
        # ----------------------------------------------------

        if result == SIMULATION_WIN:

            lifecycle.state = STATE_WIN

            return

        # ----------------------------------------------------
        # LOSS
        # ----------------------------------------------------

        if result == SIMULATION_LOSS:

            lifecycle.state = STATE_LOSS

            return

        # ----------------------------------------------------
        # AMBIGUOUS
        # ----------------------------------------------------

        if result == SIMULATION_AMBIGUOUS:

            lifecycle.state = STATE_AMBIGUOUS

            return

        # ----------------------------------------------------
        # EXPIRED
        # ----------------------------------------------------

        if result == SIMULATION_EXPIRED:

            lifecycle.state = STATE_EXPIRED

            return

        raise ValueError(
            "Resultado desconocido recibido "
            f"desde trade_simulator: {result}"
        )

    # ========================================================
    # VALIDAR SIGNAL
    # ========================================================

    @staticmethod
    def _validate_signal(
        signal: dict[str, Any],
    ) -> None:

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

        missing_fields = [

            field

            for field in required_fields

            if field not in signal
        ]

        if missing_fields:

            raise ValueError(
                "Faltan campos requeridos en signal: "
                f"{missing_fields}"
            )

        if signal["direction"] not in {
            "BUY",
            "SELL",
        }:

            raise ValueError(
                "direction debe ser BUY o SELL"
            )

        timeframe = (
            signal.get("timeframe")
            or signal.get("m5_timeframe")
        )

        if not timeframe:

            raise ValueError(
                "signal debe contener timeframe "
                "o m5_timeframe"
            )

    # ========================================================
    # OBTENER TIMEFRAME
    # ========================================================

    @staticmethod
    def _get_timeframe(
        signal: dict[str, Any],
    ) -> str:

        timeframe = signal.get(
            "timeframe"
        )

        if timeframe:

            return timeframe

        timeframe = signal.get(
            "m5_timeframe"
        )

        if timeframe:

            return timeframe

        raise ValueError(
            "No fue posible determinar el timeframe"
        )

    # ========================================================
    # VALIDAR CANDLES
    # ========================================================

    @staticmethod
    def _validate_candles(
        candles: pd.DataFrame,
    ) -> None:

        if candles is None:

            raise ValueError(
                "candles no puede ser None"
            )

        if not isinstance(
            candles,
            pd.DataFrame,
        ):

            raise TypeError(
                "candles debe ser un pandas DataFrame"
            )

        if candles.empty:

            raise ValueError(
                "candles no puede estar vacío"
            )

        required_columns = [

            "time",

            "open",

            "high",

            "low",

            "close",
        ]

        missing_columns = [

            column

            for column in required_columns

            if column not in candles.columns
        ]

        if missing_columns:

            raise ValueError(
                "Faltan columnas requeridas "
                f"en candles: {missing_columns}"
            )

    # ========================================================
    # OBTENER HISTORIAL
    # ========================================================

    def get_history(
        self,
    ) -> list[TradeLifecycle]:

        return list(
            self.lifecycle_history
        )

    # ========================================================
    # OBTENER OPERACIONES FINALIZADAS
    # ========================================================

    def get_completed_trades(
        self,
    ) -> list[TradeLifecycle]:

        return [

            lifecycle

            for lifecycle
            in self.lifecycle_history

            if lifecycle.is_final()
        ]

    # ========================================================
    # LIMPIAR HISTORIAL
    # ========================================================

    def clear_history(
        self,
    ) -> None:

        self.lifecycle_history.clear()