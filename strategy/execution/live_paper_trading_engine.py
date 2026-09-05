"""Motor de Paper Trading alimentado con precios reales del broker.

Sirve para VALIDAR la estrategia en condiciones de mercado real sin arriesgar
capital: los precios y los ticks son autenticos, pero las ordenes nunca salen
del proceso.

Es un motor SIMPLE y de proposito acotado. El motor de produccion completo es
`strategy.execution.live_trading_engine`, mucho mas extenso, con gestion de
riesgo, meta-etiquetado y cierres defensivos. Este solo encadena analisis,
ejecucion en papel y monitoreo.

Vinculaciones:
- Exige un `PaperTradeExecutor` dentro del `TradeLifecycleManager`; se niega
  a arrancar con un executor real, como salvaguarda.
- El `analyzer` suele ser el de `strategy.execution.multi_timeframe`.
- El `data_provider` es el proveedor MT5 de `brokers/`.
"""

from __future__ import annotations

from dataclasses import dataclass
import time
from typing import Any, Iterable

from strategy.execution.paper_trade_executor import PaperTradeExecutor
from trade_lifecycle_manager import STATE_EXECUTION, TradeLifecycleManager


@dataclass
class LivePaperTradingConfig:
    """Configuración del ciclo Paper Trading alimentado con precios reales.

    `monitor_before_analysis` decide el orden dentro del ciclo. Con `True`
    —el valor recomendado— primero se vigilan las posiciones abiertas y
    despues se buscan entradas nuevas, de modo que una posicion que deba
    cerrarse no espere a que termine el analisis de todos los simbolos.
    """

    volume: float = 1.0
    interval_seconds: float = 1.0
    monitor_before_analysis: bool = True


class LivePaperTradingEngine:
    """
    Orquestador funcional para validar la estrategia con datos/ticks reales
    sin enviar órdenes al broker.

    Flujo por ciclo:
        ticks reales -> monitorear posiciones Paper activas
        MultiTimeframeAnalyzer -> READY_TO_ENTER
        TradeLifecycleManager -> PaperTradeExecutor

    El proveedor debe exponer get_current_tick(symbol). El analizador debe
    exponer analyze_symbol(symbol).
    """

    def __init__(
        self,
        data_provider,
        analyzer,
        lifecycle_manager: TradeLifecycleManager,
        config: LivePaperTradingConfig | None = None,
    ):
        """Valida por adelantado todos los colaboradores y la configuración.

        La comprobacion mas importante es que el executor sea un
        `PaperTradeExecutor`: impide arrancar por error este motor de
        validacion contra una cuenta real.

        Mantiene `_processed_signal_keys` para no ejecutar dos veces la misma
        senal.

        Raises:
            TypeError: si algun colaborador no cumple su contrato.
            ValueError: si falta el executor o la configuracion es invalida.
        """
        if not isinstance(lifecycle_manager, TradeLifecycleManager):
            raise TypeError("lifecycle_manager debe ser TradeLifecycleManager")
        if lifecycle_manager.trade_executor is None:
            raise ValueError("El lifecycle_manager requiere un trade_executor")
        if not isinstance(lifecycle_manager.trade_executor, PaperTradeExecutor):
            raise TypeError("LivePaperTradingEngine requiere PaperTradeExecutor")
        if not callable(getattr(data_provider, "get_current_tick", None)):
            raise TypeError("data_provider debe implementar get_current_tick")
        if not callable(getattr(analyzer, "analyze_symbol", None)):
            raise TypeError("analyzer debe implementar analyze_symbol")

        self.data_provider = data_provider
        self.analyzer = analyzer
        self.lifecycle_manager = lifecycle_manager
        self.config = config or LivePaperTradingConfig()
        self._processed_signal_keys: set[str] = set()

        if float(self.config.volume) <= 0:
            raise ValueError("volume debe ser mayor que cero")
        if float(self.config.interval_seconds) <= 0:
            raise ValueError("interval_seconds debe ser mayor que cero")

    def run_once(self, symbols: Iterable[str]) -> dict[str, list[dict[str, Any]]]:
        """Ejecuta un ciclo completo: monitoreo y búsqueda de entradas.

        Para cada simbolo pide el analisis, descarta lo que no sea una senal
        lista, salta las ya procesadas y abre la posicion en papel.

        La clave de la senal solo se marca como procesada si la operacion
        llego de verdad a `EXECUTION` con ticket. Asi, un llenado fallido no
        bloquea el reintento en el ciclo siguiente.

        Args:
            symbols: instrumentos a evaluar en este ciclo.

        Returns:
            Dict con `monitoring` (resultados de las posiciones vigiladas) y
            `signals` (una entrada por simbolo, con su `action`:
            `NO_SIGNAL`, `DUPLICATE_SIGNAL_SKIPPED`, `PAPER_EXECUTED` o
            `PAPER_NOT_FILLED`).

        Raises:
            TypeError: si el analizador no devuelve un dict.
        """
        symbols = list(symbols)
        monitoring = []
        signals = []

        if self.config.monitor_before_analysis:
            monitoring = self.monitor_active_positions()

        for symbol in symbols:
            analysis = self.analyzer.analyze_symbol(symbol)
            if not isinstance(analysis, dict):
                raise TypeError("analyze_symbol debe devolver un dict")

            if not self._is_ready_signal(analysis):
                signals.append({
                    "symbol": symbol,
                    "action": "NO_SIGNAL",
                    "analysis": analysis,
                })
                continue

            key = self._signal_key(analysis)
            if key in self._processed_signal_keys:
                signals.append({
                    "symbol": analysis.get("symbol", symbol),
                    "action": "DUPLICATE_SIGNAL_SKIPPED",
                    "signal_key": key,
                })
                continue

            lifecycle = self.lifecycle_manager.process_signal_with_executor(
                analysis,
                volume=float(self.config.volume),
            )

            if lifecycle.state == STATE_EXECUTION and lifecycle.position_ticket:
                self._processed_signal_keys.add(key)

            signals.append({
                "symbol": lifecycle.symbol,
                "action": "PAPER_EXECUTED" if lifecycle.position_ticket else "PAPER_NOT_FILLED",
                "signal_key": key,
                "state": lifecycle.state,
                "position_ticket": lifecycle.position_ticket,
                "execution_status": lifecycle.execution_status,
                "lifecycle": lifecycle,
            })

        if not self.config.monitor_before_analysis:
            monitoring = self.monitor_active_positions()

        return {"monitoring": monitoring, "signals": signals}

    def monitor_active_positions(self) -> list[dict[str, Any]]:
        """Actualiza todas las posiciones abiertas con el tick real.

        Cachea el tick por simbolo dentro del ciclo, de modo que varias
        posiciones sobre el mismo instrumento comparten cotizacion y se evita
        pedirla repetidamente.

        Returns:
            Lista de resultados de monitoreo, enriquecidos con `symbol`,
            `market_price` y `tick_time`.
        """
        active = self.lifecycle_manager.get_active_lifecycles()
        if not active:
            return []

        ticks: dict[str, dict[str, Any]] = {}
        results: list[dict[str, Any]] = []

        for lifecycle in list(active):
            symbol = lifecycle.symbol
            if symbol not in ticks:
                ticks[symbol] = self.data_provider.get_current_tick(symbol)

            tick = ticks[symbol]
            price = self._monitor_price(lifecycle.direction, tick)
            result = self.lifecycle_manager.monitor_execution(lifecycle, price)
            result["symbol"] = symbol
            result["market_price"] = price
            result["tick_time"] = tick.get("time")
            results.append(result)

        return results

    def run_daemon(self, symbols: Iterable[str], max_cycles: int | None = None) -> None:
        """Ejecuta ciclos indefinidamente, esperando entre uno y otro.

        BLOQUEA el hilo llamante. Con `max_cycles` a `None` no termina nunca,
        lo cual es lo esperado en operativa; en tests conviene acotarlo.

        Args:
            symbols: instrumentos a vigilar.
            max_cycles: numero maximo de ciclos, o `None` para ilimitado.
        """
        cycles = 0
        while True:
            self.run_once(symbols)
            cycles += 1
            if max_cycles is not None and cycles >= int(max_cycles):
                return
            time.sleep(float(self.config.interval_seconds))

    @staticmethod
    def _monitor_price(direction: str, tick: dict[str, Any]) -> float:
        """Elige el lado del tick con el que se valoraría el cierre.

        Una compra se cierra vendiendo, asi que se valora al BID; una venta
        se cierra comprando, luego se valora al ASK. Usar el lado equivocado
        regalaria el spread en cada operacion y falsearia las metricas.

        Raises:
            ValueError: si la direccion no es `BUY` ni `SELL`.
        """
        direction = str(direction).upper()
        if direction == "BUY":
            return float(tick["bid"])
        if direction == "SELL":
            return float(tick["ask"])
        raise ValueError(f"Dirección inválida: {direction}")

    @staticmethod
    def _is_ready_signal(analysis: dict[str, Any]) -> bool:
        """Comprueba que el análisis sea una señal lista para ejecutar.

        Exige las TRES condiciones: `valid`, estado `READY_TO_ENTER` y accion
        `MULTI_TIMEFRAME_SIGNAL`. Cualquier otro analisis se ignora.

        `valid` se asume `True` si la clave no viene, ya que algunos
        analizadores solo la publican cuando invalidan.
        """
        return (
            bool(analysis.get("valid", True))
            and str(analysis.get("state", "")).upper() == "READY_TO_ENTER"
            and str(analysis.get("action", "")).upper() == "MULTI_TIMEFRAME_SIGNAL"
        )

    @staticmethod
    def _signal_key(signal: dict[str, Any]) -> str:
        """Huella de la señal para no ejecutarla dos veces.

        Combina simbolo, direccion y hora de entrada. A diferencia de la
        clave del executor NO incluye precios, asi que un mismo setup con
        stop reajustado si se detecta como repetido.

        Raises:
            ValueError: si falta alguno de los tres campos.
        """
        required = ("symbol", "direction", "entry_time")
        missing = [name for name in required if signal.get(name) is None]
        if missing:
            raise ValueError(f"Señal READY_TO_ENTER incompleta: faltan {missing}")
        return "|".join(str(signal[name]) for name in required)
