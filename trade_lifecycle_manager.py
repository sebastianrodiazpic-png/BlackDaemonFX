"""Máquina de estados del ciclo de vida de una operación, de la señal al cierre.

Es la capa que convierte una senal ya validada en una operacion con estado
explicito y trazable. Modela el recorrido completo:

    READY_TO_ENTER -> EXECUTION -> {WIN, LOSS, AMBIGUOUS, EXPIRED,
                                    BREAK_EVEN, CLOSED}

Los estados de la segunda fila son FINALES: una vez alcanzados el lifecycle
no admite mas transiciones y cualquier intento lanza `RuntimeError`. Esa
rigidez es intencionada, porque evita que una operacion ya liquidada se
reejecute o se cierre dos veces.

Ofrece DOS caminos de ejecucion mutuamente independientes:

1. Backtest: `execute` / `process_signal`, que resuelven el desenlace de un
   golpe llamando al `trade_simulator` sobre un DataFrame de velas.
2. Operativa real o papel: `execute_with_executor` /
   `process_signal_with_executor`, que abren la posicion mediante un
   `TradeExecutor` y luego requieren llamadas repetidas a `monitor_execution`
   hasta que la posicion se cierre.

El constructor exige al menos uno de los dos colaboradores.

Vinculaciones:
- Importa el contrato `TradeExecutor` y sus tipos desde
  `strategy.execution.trade_executor`.
- La implementacion de papel es
  `strategy.execution.paper_trade_executor.PaperTradeExecutor`.
- `monitoring.position_monitoring_service` invoca `monitor_open_executions`
  en bucle para vigilar las posiciones vivas.
- `_notify_reporting` emite eventos al `reporting_service` inyectado, que en
  produccion es el servicio de reporte de operaciones.
- `strategy.execution.live_paper_trading_engine` y `app.main` lo instancian.
- El `trade_simulator` que recibe es `strategy.smc.trade_simulator.simulate_trade`
  o su homonimo de `backtesting`; son funciones distintas, comprobar cual se
  esta inyectando.
"""

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
    """Estado completo de una operación individual a lo largo de su vida.

    Es un objeto MUTABLE que se va enriqueciendo: nace en `READY_TO_ENTER`
    con solo los datos de la senal y acumula precio de entrada real, ticket,
    salida y resultado conforme avanza.

    Ojo con `entry_price`, `stop_loss` y `take_profit`: al ejecutar contra un
    broker se SOBRESCRIBEN con los valores realmente llenados, que pueden
    diferir de los planificados por deslizamiento.

    `metadata` es el saco libre donde viajan datos auxiliares (volumen,
    broker, motivo de ejecucion) y es lo que se persiste para auditoria.
    """

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
        """Indica si el lifecycle ya alcanzó un estado terminal.

        Los metodos de ejecucion y cierre lo consultan primero para negarse a
        operar sobre una operacion ya liquidada.
        """
        return self.state in FINAL_STATES

    def to_dict(self) -> dict[str, Any]:
        """Vuelca el lifecycle a un dict plano para persistir o reportar.

        Vinculaciones:
        - Lo usa `_notify_reporting` en la carga util de cada evento.
        """
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
    """Orquesta la creación, ejecución, monitoreo y cierre de lifecycles.

    Mantiene dos colecciones:
    - `_active_lifecycles`: indexada por ticket de posicion, solo operaciones
      vivas. Se limpia al cerrar.
    - `lifecycle_history`: acumula TODOS los lifecycles finalizados.

    Vinculaciones:
    - Lo instancian `strategy.execution.live_paper_trading_engine` y `app.main`.
    - `monitoring.position_monitoring_service` llama a `monitor_open_executions`.
    """

    def __init__(
        self,
        trade_simulator: Optional[Callable[..., dict[str, Any]]] = None,
        trade_executor: Optional[TradeExecutor] = None,
        reporting_service: Optional[Any] = None,
    ):
        """Inyecta los colaboradores y valida sus contratos por adelantado.

        Se exige AL MENOS uno entre `trade_simulator` y `trade_executor`: sin
        ninguno de los dos el manager no podria resolver ninguna operacion.
        Se pueden dar los dos, y entonces cada metodo usa el que le
        corresponde.

        Args:
            trade_simulator: callable de backtest que resuelve el desenlace
                sobre un DataFrame de velas.
            trade_executor: implementacion de `TradeExecutor` para operativa
                real o papel.
            reporting_service: objeto opcional con `on_lifecycle_event`, al
                que se notifica cada transicion relevante.

        Raises:
            TypeError: si algun colaborador no cumple su contrato.
            ValueError: si no se proporciona simulador ni executor.
        """
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
        """Construye un lifecycle en `READY_TO_ENTER` desde una señal validada.

        NO ejecuta nada: solo traduce el dict de senal a un objeto con estado.
        Valida antes los campos obligatorios y la coherencia de precios.

        Args:
            signal: dict con `symbol`, `direction`, `entry_time`,
                `entry_price`, `stop_loss` y `take_profit`.

        Returns:
            El lifecycle listo para ejecutar.

        Raises:
            ValueError o TypeError si la senal es incompleta o incoherente.

        Vinculaciones:
        - Delega la validacion en `_validate_signal` y `_get_timeframe`.
        """
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
        """Resuelve el lifecycle de golpe simulando sobre velas históricas.

        Camino de BACKTEST, no de operativa real. Pasa por `EXECUTION` y
        alcanza el estado final en una sola llamada: el simulador recorre las
        velas y determina si toco antes el TP o el SL.

        Convierte la direccion `BUY`/`SELL` al vocabulario `long`/`short` que
        espera el simulador.

        Args:
            lifecycle: operacion en estado no final.
            candles: velas POSTERIORES a la entrada.
            max_bars: limite de velas antes de declarar la operacion expirada.

        Returns:
            El mismo lifecycle, ya finalizado y registrado en el historial.

        Raises:
            RuntimeError: si el lifecycle ya es final, si no hay simulador
                configurado o si el simulador devuelve algo invalido.

        Vinculaciones:
        - Llama al `trade_simulator` inyectado y notifica
          `LIFECYCLE_FINALIZED` al servicio de reporte.
        """
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
        """Atajo de backtest: crea el lifecycle desde la señal y lo ejecuta.

        Equivale a `create_from_signal` seguido de `execute`. Es el punto de
        entrada habitual del motor de backtest.
        """
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
        """Abre la posición en el broker real o de papel.

        A diferencia de `execute`, NO finaliza la operacion: la deja en
        `EXECUTION` y registrada en `_active_lifecycles`, a la espera de que
        `monitor_execution` detecte su cierre.

        Detalle critico: tras el llenado se SOBRESCRIBEN `entry_price`,
        `stop_loss` y `take_profit` con los precios realmente ejecutados, que
        pueden diferir por deslizamiento.

        Si la orden se rechaza, el lifecycle NO cambia de estado, se marca
        `execution_accepted` en metadata y se emite `EXECUTION_REJECTED`; el
        lifecycle sigue siendo reutilizable.

        Args:
            lifecycle: operacion en estado no final y sin posicion abierta.
            volume: tamano de la posicion.
            trade_executor: executor puntual; si se omite usa el del manager.

        Returns:
            El lifecycle actualizado, llenado o rechazado.

        Raises:
            RuntimeError: si el lifecycle es final, ya tiene posicion activa,
                no hay executor, o el executor llena sin devolver ticket.

        Vinculaciones:
        - Construye un `TradeExecutionRequest` y espera un
          `TradeExecutionResult`, ambos de `strategy.execution.trade_executor`.
        - Emite `EXECUTION_FILLED` o `EXECUTION_REJECTED`.
        """
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

        lifecycle.metadata["requested_volume"] = float(volume)
        lifecycle.metadata["volume"] = float(result.volume)
        if result.metadata.get("risk_resize"):
            lifecycle.metadata["risk_resize"] = result.metadata["risk_resize"]
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
            volume=float(result.volume),
        )
        return lifecycle

    def process_signal_with_executor(
        self,
        signal: dict[str, Any],
        volume: float = 1.0,
        trade_executor: Optional[TradeExecutor] = None,
    ) -> TradeLifecycle:
        """Atajo de operativa: crea el lifecycle y abre la posición.

        Equivale a `create_from_signal` seguido de `execute_with_executor`.
        Recuerda que la operacion queda ABIERTA y necesita monitoreo.
        """
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
        """Cierra una posición activa mediante el executor y finaliza el lifecycle.

        Es el cierre DELIBERADO, distinto del que detecta `monitor_execution`
        cuando el mercado toca SL o TP. Lo usan los cierres defensivos del
        gestor y las paradas manuales.

        Solo confia en el executor: si `close_position` no confirma
        `closed=True` aborta sin tocar el estado, para no dar por cerrada en
        el bot una posicion que sigue viva en el broker.

        Args:
            lifecycle: operacion en `EXECUTION` con ticket asignado.
            trade_executor: executor puntual; si se omite usa el del manager.
            reason: motivo del cierre, que determina el estado final via
                `_state_from_exit_reason`. Conviene que sea especifico para
                poder auditar despues por que se cerro.

        Returns:
            El dict crudo devuelto por el executor.

        Raises:
            RuntimeError: si el lifecycle es final, no tiene posicion activa,
                no hay executor o el cierre no se confirma.
        """
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
        """Refresca una posición abierta y la finaliza si el broker la cerró.

        Es el latido de la operativa: se llama repetidamente con el precio
        vivo. Cada llamada delega en `monitor_position` del executor, que es
        quien aplica trailing y break-even y decide si la posicion se ha
        cerrado.

        Dos desenlaces:
        - Sigue abierta: sincroniza SL, TP y flotante en el lifecycle y emite
          `POSITION_UPDATED`.
        - Se cerro: traduce el motivo de salida a resultado y estado final,
          la saca de `_active_lifecycles`, la archiva en el historial y emite
          `LIFECYCLE_FINALIZED`.

        Args:
            lifecycle: operacion en `EXECUTION` con ticket.
            current_price: precio actual del instrumento.
            trade_executor: executor puntual; si se omite usa el del manager.

        Returns:
            El dict crudo del executor, con al menos la clave `closed`.

        Raises:
            RuntimeError: si el lifecycle es final o no tiene posicion activa.
            TypeError: si el executor no soporta `monitor_position` o su
                respuesta no es un dict.

        Vinculaciones:
        - Lo invoca en bucle `monitor_open_executions`, y a traves de el
          `monitoring.position_monitoring_service`.
        """
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
        """Monitorea en lote todas las posiciones vivas con precio disponible.

        Los tickets sin precio en el dict se SALTAN en silencio, de modo que
        una cotizacion ausente no interrumpe el ciclo de las demas. Itera
        sobre una copia de la coleccion porque `monitor_execution` puede
        eliminar entradas al cerrar.

        Args:
            prices_by_ticket: precio actual indexado por ticket de posicion.

        Returns:
            Un dict de resultado por cada posicion monitoreada.

        Vinculaciones:
        - Es el metodo que llama `monitoring.position_monitoring_service` en
          su bucle de vigilancia.
        """
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
        """Recupera el lifecycle vivo asociado a un ticket, o None."""
        return self._active_lifecycles.get(str(position_ticket))

    def get_active_lifecycles(self) -> list[TradeLifecycle]:
        """Devuelve una copia de la lista de operaciones actualmente abiertas."""
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

        Eventos emitidos: `EXECUTION_FILLED`, `EXECUTION_REJECTED`,
        `POSITION_UPDATED` y `LIFECYCLE_FINALIZED`.

        Si no hay servicio inyectado no hace nada, de modo que el manager
        funciona igual en tests y backtests sin persistencia.
        """
        if self.reporting_service is None:
            return None

        return self.reporting_service.on_lifecycle_event(
            event=event,
            lifecycle=lifecycle,
            volume=volume,
        )

    def _record_final_lifecycle(self, lifecycle: TradeLifecycle) -> None:
        """Archiva el lifecycle en el historial, evitando duplicados.

        Comprueba identidad de objeto (`is`), no igualdad, porque dos
        operaciones distintas pueden tener campos identicos. Solo archiva si
        el estado es final.
        """
        if lifecycle.is_final() and not any(item is lifecycle for item in self.lifecycle_history):
            self.lifecycle_history.append(lifecycle)

    @staticmethod
    def _result_from_exit_reason(exit_reason: str) -> str:
        """Traduce el motivo de salida al vocabulario de resultado.

        Los motivos desconocidos se devuelven TAL CUAL en lugar de caer en un
        valor por defecto, para no ocultar en el reporte una causa de cierre
        no contemplada.
        """
        mapping = {
            "take_profit": "win",
            "stop_loss": "loss",
            "break_even_stop": "break_even",
            "manual_close": "closed",
        }
        return mapping.get(str(exit_reason), str(exit_reason))

    @staticmethod
    def _state_from_exit_reason(exit_reason: str) -> str:
        """Traduce el motivo de salida al estado final del lifecycle.

        A diferencia de `_result_from_exit_reason`, aqui SI hay valor por
        defecto: cualquier motivo no contemplado cae en `CLOSED`, que es un
        estado final generico y seguro.

        NOTA: por eso los cierres defensivos del gestor terminan mostrandose
        como `CLOSED` en el reporte; el motivo detallado se conserva en
        `lifecycle.exit_reason`, no en el estado.
        """
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
        """Vuelca el desenlace del simulador sobre el lifecycle.

        Copia salida, barras aguantadas y PnL, y traduce el resultado del
        simulador (`win`, `loss`, `ambiguous`, `expired`) al estado final
        correspondiente.

        `ambiguous` significa que dentro de la misma vela se tocaron SL y TP
        y no se puede saber cual ocurrio primero; se marca como tal en vez de
        elegir arbitrariamente, para no falsear las estadisticas.

        Raises:
            ValueError: ante un resultado desconocido. Falla en voz alta a
                proposito, ya que un desenlace no contemplado corromperia las
                metricas si se ignorase.
        """
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
        """Valida que la señal traiga todo lo necesario antes de crear nada.

        Comprueba tipo, campos obligatorios, que la direccion sea `BUY` o
        `SELL`, y que exista timeframe en alguna de sus dos claves posibles.

        Falla rapido y con mensaje explicito: es preferible rechazar la senal
        aqui que crear un lifecycle a medias que reviente al ejecutarse.

        Raises:
            TypeError: si `signal` no es un dict.
            ValueError: si faltan campos, la direccion es invalida o no hay
                timeframe.
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
        """Obtiene el timeframe de la señal, con `timeframe` sobre `m5_timeframe`.

        La doble clave existe porque las estrategias no publican el campo con
        el mismo nombre. `_validate_signal` ya garantiza que hay uno.

        Raises:
            ValueError: si ninguna de las dos claves esta presente.
        """
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
        """Comprueba que el DataFrame de velas sirve para simular.

        Exige DataFrame no vacio con las columnas OHLC y de tiempo. Sin esta
        barrera el simulador fallaria mas adelante con errores opacos de
        pandas, dificiles de rastrear hasta la senal culpable.

        Raises:
            ValueError o TypeError describiendo el problema concreto.
        """
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
        """Devuelve una copia superficial del historial de lifecycles.

        La lista es nueva, pero los lifecycles son los mismos objetos:
        modificarlos afecta al historial real.
        """
        return list(
            self.lifecycle_history
        )

    # ========================================================
    # OBTENER OPERACIONES FINALIZADAS
    # ========================================================

    def get_completed_trades(
        self,
    ) -> list[TradeLifecycle]:
        """Filtra del historial solo las operaciones en estado final.

        En la practica coincide con `get_history`, porque
        `_record_final_lifecycle` solo archiva lifecycles finalizados; el
        filtro es una salvaguarda por si algo se anade a mano.
        """
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
        """Vacía el historial de lifecycles finalizados.

        NO afecta a `_active_lifecycles`: las posiciones abiertas siguen
        vigiladas. Pensado para liberar memoria entre tandas de backtest.
        """
        self.lifecycle_history.clear()