"""Despachador de Eventos Asíncrono y Arquitectura Orientada a Eventos (Event-Driven).

Inspirado en plataformas de trading institucional como NautilusTrader.
Reemplaza los bucles rígidos de sondeo (`while True: sleep(...)`) con una cola de
mensajes concurrente y reactiva donde los módulos de mercado, análisis SMC,
gestión de riesgo y ejecución de órdenes interactúan mediante eventos desacoplados.

Ventajas:
1. Reacción sub-segundo ante cierres de vela y ticks sin esperar al final del sleep.
2. Priorización de eventos críticos (ej. alertas de riesgo o SL antes de análisis).
3. Soporte para callbacks síncronos y corrutinas asíncronas (asyncio).
4. Métricas completas de latencia y trazabilidad de eventos.
"""
from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from enum import Enum
import logging
import queue
import threading
import time
from typing import Any, Callable, Coroutine, Dict, List, Optional, Union

logger = logging.getLogger("strategy.execution.event_dispatcher")


class EventType(str, Enum):
    """Tipos de eventos soportados en el bus del sistema."""
    TICK = "TICK"
    BAR_CLOSED = "BAR_CLOSED"
    STRUCTURE_BREAK = "STRUCTURE_BREAK"
    SIGNAL_GENERATED = "SIGNAL_GENERATED"
    ORDER_SUBMITTED = "ORDER_SUBMITTED"
    ORDER_FILLED = "ORDER_FILLED"
    ORDER_CLOSED = "ORDER_CLOSED"
    RISK_ALERT = "RISK_ALERT"
    TIMER = "TIMER"
    SYSTEM_SHUTDOWN = "SYSTEM_SHUTDOWN"


@dataclass(frozen=True)
class Event:
    """Evento base inmutable para el despachador."""
    event_type: EventType
    timestamp: float = field(default_factory=time.time)
    data: Dict[str, Any] = field(default_factory=dict)
    priority: int = 10  # Menor número = mayor prioridad (0 = máxima urgencia)

    def __lt__(self, other: Event) -> bool:
        return self.priority < other.priority


@dataclass(frozen=True)
class TickEvent(Event):
    """Evento de cotización de tick en tiempo real."""
    def __init__(self, symbol: str, bid: float, ask: float, timestamp: float | None = None):
        super().__init__(
            event_type=EventType.TICK,
            timestamp=timestamp or time.time(),
            data={"symbol": symbol, "bid": bid, "ask": ask},
            priority=5,
        )


@dataclass(frozen=True)
class BarClosedEvent(Event):
    """Evento de cierre de vela en un marco temporal específico."""
    def __init__(self, symbol: str, timeframe: str, bar: dict, timestamp: float | None = None):
        super().__init__(
            event_type=EventType.BAR_CLOSED,
            timestamp=timestamp or time.time(),
            data={"symbol": symbol, "timeframe": timeframe, "bar": bar},
            priority=3,
        )


@dataclass(frozen=True)
class SignalEvent(Event):
    """Evento de setup SMC validado por confirmation_engine."""
    def __init__(self, symbol: str, direction: str, score: float, candidate: dict):
        super().__init__(
            event_type=EventType.SIGNAL_GENERATED,
            timestamp=time.time(),
            data={"symbol": symbol, "direction": direction, "score": score, "candidate": candidate},
            priority=2,
        )


@dataclass(frozen=True)
class RiskAlertEvent(Event):
    """Evento crítico de gestión de riesgo o parada de emergencia."""
    def __init__(self, symbol: str, reason: str, action: str = "PAUSE"):
        super().__init__(
            event_type=EventType.RISK_ALERT,
            timestamp=time.time(),
            data={"symbol": symbol, "reason": reason, "action": action},
            priority=0,  # Máxima prioridad absoluta
        )


HandlerType = Union[Callable[[Event], Any], Callable[[Event], Coroutine[Any, Any, Any]]]


class AsyncEventDispatcher:
    """Despachador central de eventos thread-safe con soporte para handlers síncronos y asíncronos."""

    def __init__(self, max_queue_size: int = 5000):
        self._sync_subscribers: Dict[EventType, List[Callable[[Event], Any]]] = {}
        self._async_subscribers: Dict[EventType, List[Callable[[Event], Coroutine[Any, Any, Any]]]] = {}
        self._priority_queue: queue.PriorityQueue = queue.PriorityQueue(maxsize=max_queue_size)
        self._running = False
        self._worker_thread: Optional[threading.Thread] = None
        self._lock = threading.RLock()
        self._event_count = 0
        self._processing_latencies: List[float] = []

    def subscribe(self, event_type: EventType, handler: HandlerType):
        """Registra un receptor para un tipo específico de evento."""
        with self._lock:
            if asyncio.iscoroutinefunction(handler):
                self._async_subscribers.setdefault(event_type, []).append(handler)
            else:
                self._sync_subscribers.setdefault(event_type, []).append(handler)
        logger.debug("Suscrito handler a evento %s", event_type.value)

    def publish(self, event: Event):
        """Encola un evento para su procesamiento asíncrono ordenado por prioridad."""
        try:
            self._priority_queue.put_nowait(event)
            self._event_count += 1
        except queue.Full:
            logger.error("Cola de eventos saturada. Descartando evento prioritario %s", event.event_type)

    def start(self):
        """Inicia el despachador en un hilo de fondo dedicado."""
        with self._lock:
            if self._running:
                return
            self._running = True
            self._worker_thread = threading.Thread(target=self._dispatch_loop, daemon=True, name="EventDispatcher")
            self._worker_thread.start()
            logger.info("Despachador de eventos asíncrono iniciado.")

    def stop(self, timeout: float = 2.0):
        """Detiene el despachador de eventos."""
        with self._lock:
            if not self._running:
                return
            self._running = False
            self.publish(Event(event_type=EventType.SYSTEM_SHUTDOWN, priority=0))

        if self._worker_thread and self._worker_thread.is_alive():
            self._worker_thread.join(timeout=timeout)
        logger.info("Despachador de eventos detenido.")

    def _dispatch_loop(self):
        """Bucle principal de despacho concurrente."""
        while self._running:
            try:
                event: Event = self._priority_queue.get(timeout=0.2)
            except queue.Empty:
                continue

            if event.event_type == EventType.SYSTEM_SHUTDOWN:
                break

            t0 = time.perf_counter()
            self._process_event(event)
            t1 = time.perf_counter()

            latency_ms = (t1 - t0) * 1000.0
            if len(self._processing_latencies) < 500:
                self._processing_latencies.append(latency_ms)
            self._priority_queue.task_done()

    def _process_event(self, event: Event):
        """Ejecuta todos los callbacks síncronos y asíncronos suscritos al evento."""
        # 1. Callbacks síncronos
        sync_handlers = self._sync_subscribers.get(event.event_type, [])
        for handler in sync_handlers:
            try:
                handler(event)
            except Exception as exc:
                logger.error("Error en handler síncrono para %s: %s", event.event_type, exc, exc_info=True)

        # 2. Corrutinas asíncronas
        async_handlers = self._async_subscribers.get(event.event_type, [])
        if async_handlers:
            try:
                loop = asyncio.get_event_loop()
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)

            for a_handler in async_handlers:
                try:
                    if loop.is_running():
                        asyncio.run_coroutine_threadsafe(a_handler(event), loop)
                    else:
                        loop.run_until_complete(a_handler(event))
                except Exception as exc:
                    logger.error("Error en corrutina asíncrona para %s: %s", event.event_type, exc)

    def stats(self) -> dict:
        """Estadísticas del despachador."""
        with self._lock:
            avg_lat = sum(self._processing_latencies) / max(1, len(self._processing_latencies))
            return {
                "total_events_dispatched": self._event_count,
                "pending_queue_size": self._priority_queue.qsize(),
                "avg_dispatch_latency_ms": round(avg_lat, 3),
            }
