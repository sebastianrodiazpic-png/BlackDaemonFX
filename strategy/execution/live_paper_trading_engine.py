from __future__ import annotations

from dataclasses import dataclass
import time
from typing import Any, Iterable

from strategy.execution.paper_trade_executor import PaperTradeExecutor
from trade_lifecycle_manager import STATE_EXECUTION, TradeLifecycleManager


@dataclass
class LivePaperTradingConfig:
    """Configuración del ciclo Paper Trading alimentado con precios reales."""

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
        cycles = 0
        while True:
            self.run_once(symbols)
            cycles += 1
            if max_cycles is not None and cycles >= int(max_cycles):
                return
            time.sleep(float(self.config.interval_seconds))

    @staticmethod
    def _monitor_price(direction: str, tick: dict[str, Any]) -> float:
        direction = str(direction).upper()
        if direction == "BUY":
            return float(tick["bid"])
        if direction == "SELL":
            return float(tick["ask"])
        raise ValueError(f"Dirección inválida: {direction}")

    @staticmethod
    def _is_ready_signal(analysis: dict[str, Any]) -> bool:
        return (
            bool(analysis.get("valid", True))
            and str(analysis.get("state", "")).upper() == "READY_TO_ENTER"
            and str(analysis.get("action", "")).upper() == "MULTI_TIMEFRAME_SIGNAL"
        )

    @staticmethod
    def _signal_key(signal: dict[str, Any]) -> str:
        required = ("symbol", "direction", "entry_time")
        missing = [name for name in required if signal.get(name) is None]
        if missing:
            raise ValueError(f"Señal READY_TO_ENTER incompleta: faltan {missing}")
        return "|".join(str(signal[name]) for name in required)
