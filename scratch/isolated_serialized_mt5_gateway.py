"""
Prototipo Aislado de Acceso Serializado a MetaTrader 5 (MT5 Serialized Gateway v2)
BlackDaemonFx - Entorno de Investigación Aislado (Mocks / Staging / Datos Archivados)

Mejoras incorporadas:
1. Cola Priorizada Dual (Anti-Starvation FIFO):
   - PRIORITY_CRITICAL (1): Órdenes de mercado, cierres de emergencia y order_check.
   - PRIORITY_DATA (2): Consultas de velas históricas y cotizaciones.
   - Política Anti-Starvation: Tras 'max_consecutive_critical' peticiones prioritarias
     consecutivas (por defecto 5), el worker atiende obligatoriamente una petición de datos
     pendiente si existe, evitando la inanición del análisis técnico.
   - Garantía de orden FIFO estricto dentro de cada nivel de prioridad.
2. Expiración de Peticiones Obsoletas (TTL):
   - Cada petición puede tener un 'ttl_seconds'.
   - Si la petición expira mientras espera en cola, el worker la descarta ANTES de enviarla
     al conector MT5, resolviendo el Future con TimeoutError y ahorrando I/O innecesario.
3. Reconexión y Reintentos Bounded ante Fallos IPC:
   - Captura excepciones transitorias de conexión (ConnectionResetError, ConnectionError, BrokenPipeError).
   - Reintenta hasta 'max_retries' con backoff progresivo y hook de reconexión simulada ('reconnect').
   - Límite estricto de reintentos para evitar bucles infinitos; tras agotar reintentos,
     propaga el error al Future y continúa atendiendo la cola normalmente.
4. No Interrupción de Operaciones en Vuelo:
   - El worker monohilo procesa cada llamada hasta completarse; una orden prioritaria que llega
     se coloca al frente de la cola de espera, pero NO interrumpe la llamada MT5 en curso.
5. Verificación Estricta de Concurrencia:
   - 'MockMT5Connector' audita en tiempo real que NUNCA haya más de 1 llamada simultánea al conector.
"""

from __future__ import annotations

import time
import queue
import threading
from concurrent.futures import Future, TimeoutError
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple

import pandas as pd

# ---------------------------------------------------------------------------
# Constantes de Prioridad
# ---------------------------------------------------------------------------
PRIORITY_CRITICAL = 1  # Órdenes de trading y acciones urgentes
PRIORITY_DATA = 2      # Descarga de velas y consultas de mercado

DEFAULT_MAX_CONSECUTIVE_CRITICAL = 5
DEFAULT_MAX_RETRIES = 2
DEFAULT_RETRY_BACKOFF_SEC = 0.02


# ---------------------------------------------------------------------------
# 1. Conector Simulado de MT5 con Auditoría de Concurrencia y Reconexión
# ---------------------------------------------------------------------------

class ConcurrencyViolationError(RuntimeError):
    """Lanzada si se detecta más de una llamada simultánea al conector MT5."""
    pass


class BrokerIPCError(ConnectionError):
    """Error transitorio simulado de desconexión IPC con el terminal MT5 (Reintentable)."""
    pass


class MT5BusinessError(RuntimeError):
    """Error permanente de negocio/terminal en MT5 (NO reintentable).
    Ejemplos: 10027 (AutoTrading disabled by client), 10018 (Market closed).
    NUNCA debe disparar reintentos ni reconexiones IPC."""
    def __init__(self, retcode: int, message: str):
        super().__init__(f"MT5 Business Error [{retcode}]: {message}")
        self.retcode = retcode
        self.message = message


class ExposureRejectionError(RuntimeError):
    """Lanzada cuando una solicitud viola la política de exposición activa o en vuelo."""
    def __init__(self, symbol: str, status: str, reason: str):
        super().__init__(f"EXPOSURE_GUARD_REJECTION [{status}] for {symbol}: {reason}")
        self.symbol = symbol
        self.status = status
        self.reason = reason


# Códigos de error definitivos de MT5 que NO admiten reintentos ni reconexión (Permanentes / Negocio)
NON_RETRYABLE_RETCODES = {
    10013: "TRADE_RETCODE_INVALID",
    10014: "TRADE_RETCODE_INVALID_VOLUME",
    10015: "TRADE_RETCODE_INVALID_PRICE",
    10016: "TRADE_RETCODE_INVALID_STOPS",
    10017: "TRADE_RETCODE_TRADE_DISABLED",
    10018: "TRADE_RETCODE_MARKET_CLOSED",
    10019: "TRADE_RETCODE_NO_MONEY",
    10022: "TRADE_RETCODE_INVALID_EXPIRATION",
    10026: "TRADE_RETCODE_SERVER_DISABLES_AT",
    10027: "TRADE_RETCODE_CLIENT_DISABLES_AT",
    10030: "TRADE_RETCODE_INVALID_FILL",
    10032: "TRADE_RETCODE_ONLY_REAL",
    10033: "TRADE_RETCODE_LIMIT_ORDERS",
    10034: "TRADE_RETCODE_LIMIT_VOLUME",
}

# Códigos de error transitorios de MT5 devueltos como retcode que admiten reintentos limitados
RETRYABLE_RETCODES = {
    10004: "TRADE_RETCODE_REQUOTE",
    10020: "TRADE_RETCODE_PRICE_CHANGED",
    10024: "TRADE_RETCODE_TOO_MANY_REQUESTS",
    10031: "TRADE_RETCODE_CONNECTION",
}


class MockMT5Connector:
    """Simulador de terminal MT5 que audita la concurrencia, simula reconexiones y gestiona estado."""

    def __init__(
        self,
        cached_dfs: Optional[Dict[str, pd.DataFrame]] = None,
        io_delay_sec: float = 0.02,
        fail_next_n_calls: int = 0,
    ):
        self.cached_dfs = cached_dfs or {}
        self.io_delay_sec = io_delay_sec
        self.fail_next_n_calls = fail_next_n_calls
        self._active_calls = 0
        self._max_observed_concurrency = 0
        self._lock = threading.Lock()
        self.call_log: List[Dict[str, Any]] = []
        self.reconnect_count = 0
        self.is_connected = True

        # Estado simulado de posiciones y órdenes para Exposure Guard
        self.open_positions: List[Dict[str, Any]] = []
        self.pending_orders: List[Dict[str, Any]] = []

    def get_open_positions(self) -> List[Dict[str, Any]]:
        with self._lock:
            return list(self.open_positions)

    def get_pending_orders(self) -> List[Dict[str, Any]]:
        with self._lock:
            return list(self.pending_orders)

    def add_open_position(self, pos: Dict[str, Any]) -> None:
        with self._lock:
            self.open_positions.append(dict(pos))

    def clear_positions_and_orders(self) -> None:
        with self._lock:
            self.open_positions.clear()
            self.pending_orders.clear()

    def reconnect(self) -> bool:
        """Simula el restablecimiento de la conexión IPC con el terminal."""
        with self._lock:
            self.reconnect_count += 1
            self.is_connected = True
            return True

    def _enter_call(self, method_name: str, symbol: str) -> None:
        with self._lock:
            self._active_calls += 1
            if self._active_calls > self._max_observed_concurrency:
                self._max_observed_concurrency = self._active_calls
            current_active = self._active_calls

        if current_active > 1:
            raise ConcurrencyViolationError(
                f"VIOLACIÓN DE CONCURRENCIA MT5: {current_active} llamadas simultáneas detectadas en {method_name} ({symbol})!"
            )

        # Inyección de fallos IPC simulados
        with self._lock:
            if self.fail_next_n_calls > 0:
                self.fail_next_n_calls -= 1
                self.is_connected = False
                raise BrokerIPCError(f"Simulated MT5 IPC Pipe Broken on {method_name}({symbol})")

    def _exit_call(self, method_name: str, symbol: str, start_time: float, error: Optional[Exception] = None) -> None:
        elapsed = time.perf_counter() - start_time
        with self._lock:
            self._active_calls -= 1
            self.call_log.append({
                "method": method_name,
                "symbol": symbol,
                "elapsed_s": elapsed,
                "error": type(error).__name__ if error else None,
                "timestamp": time.time(),
            })

    def copy_rates_from_pos(self, symbol: str, timeframe: str, start_pos: int, count: int) -> pd.DataFrame:
        t0 = time.perf_counter()
        err = None
        try:
            self._enter_call("copy_rates_from_pos", symbol)
            if self.io_delay_sec > 0:
                time.sleep(self.io_delay_sec)

            df = self.cached_dfs.get(symbol)
            if df is not None:
                return df.tail(count).copy()
            # Retorno sintético básico si no hay datos archivados
            return pd.DataFrame({
                "time": [datetime.now(timezone.utc)] * count,
                "open": [100.0] * count,
                "high": [101.0] * count,
                "low": [99.0] * count,
                "close": [100.5] * count,
                "tick_volume": [10] * count,
            })
        except Exception as exc:
            err = exc
            raise
        finally:
            self._exit_call("copy_rates_from_pos", symbol, t0, err)

    def order_send(self, request: Dict[str, Any]) -> Dict[str, Any]:
        t0 = time.perf_counter()
        symbol = str(request.get("symbol", "UNKNOWN"))
        err = None
        try:
            self._enter_call("order_send", symbol)
            if self.io_delay_sec > 0:
                time.sleep(self.io_delay_sec)

            # Inyección configurable de errores de negocio MT5 (10027, 10018, etc.)
            mock_retcode = request.get("mock_retcode")
            if mock_retcode is not None and mock_retcode != 10009:
                err_msg = NON_RETRYABLE_RETCODES.get(mock_retcode, f"Trade error {mock_retcode}")
                if request.get("raise_business_error", False):
                    raise MT5BusinessError(mock_retcode, err_msg)
                return {
                    "retcode": mock_retcode,
                    "deal": 0,
                    "order": 0,
                    "comment": err_msg,
                }

            return {
                "retcode": 10009,  # TRADE_RETCODE_DONE
                "deal": 123456,
                "order": 654321,
                "volume": request.get("volume", 0.01),
                "price": request.get("price", 100.0),
                "comment": "Mock trade executed",
            }
        except Exception as exc:
            err = exc
            raise
        finally:
            self._exit_call("order_send", symbol, t0, err)


# ---------------------------------------------------------------------------
# 2. Petición del Gateway con Prioridad, TTL y Reintentos
# ---------------------------------------------------------------------------

@dataclass
class GatewayRequest:
    req_id: int
    func: Callable[..., Any]
    args: Tuple[Any, ...]
    kwargs: Dict[str, Any]
    future: Future
    submitted_at: float
    priority: int = PRIORITY_DATA
    ttl_seconds: Optional[float] = None
    max_retries: int = DEFAULT_MAX_RETRIES
    completed_at: Optional[float] = None
    latency_ms: Optional[float] = None
    error: Optional[str] = None
    was_discarded_ttl: bool = False

    def is_expired(self) -> bool:
        if self.ttl_seconds is None or self.ttl_seconds <= 0:
            return False
        return (time.perf_counter() - self.submitted_at) > self.ttl_seconds


# ---------------------------------------------------------------------------
# 3. Gateway Serializado con Prioridad, Anti-Starvation y Reintentos
# ---------------------------------------------------------------------------

class SerializedMT5Gateway:
    """Canalizador monohilo priorizado hacia MetaTrader 5 con TTL y reconexión."""

    def __init__(
        self,
        connector: MockMT5Connector,
        max_consecutive_critical: int = DEFAULT_MAX_CONSECUTIVE_CRITICAL,
        default_max_retries: int = DEFAULT_MAX_RETRIES,
        retry_backoff_sec: float = DEFAULT_RETRY_BACKOFF_SEC,
    ):
        self.connector = connector
        self.max_consecutive_critical = max_consecutive_critical
        self.default_max_retries = default_max_retries
        self.retry_backoff_sec = retry_backoff_sec

        # Colas duales FIFO estrictas por nivel de prioridad
        self._critical_queue: queue.Queue[Optional[GatewayRequest]] = queue.Queue()
        self._data_queue: queue.Queue[Optional[GatewayRequest]] = queue.Queue()
        self._cv = threading.Condition()

        self._counter = 0
        self._counter_lock = threading.Lock()
        self._shutdown_event = threading.Event()
        self._consecutive_critical_served = 0

        # Métricas de auditoría y telemetría de latencia
        self.processed_requests_log: List[int] = []
        self.expired_requests_log: List[int] = []
        self.completed_requests: List[GatewayRequest] = []
        self.retried_requests_count = 0
        self.failed_requests_count = 0

        self._worker_thread = threading.Thread(
            target=self._process_queue_loop,
            name="MT5SerializedWorker",
            daemon=True,
        )
        self._worker_thread.start()

    def submit(
        self,
        func: Callable[..., Any],
        *args,
        priority: int = PRIORITY_DATA,
        ttl_seconds: Optional[float] = None,
        max_retries: Optional[int] = None,
        **kwargs,
    ) -> Future:
        if self._shutdown_event.is_set():
            fut = Future()
            fut.set_exception(RuntimeError("El Gateway MT5 está apagado"))
            return fut

        with self._counter_lock:
            self._counter += 1
            req_id = self._counter

        fut = Future()
        req = GatewayRequest(
            req_id=req_id,
            func=func,
            args=args,
            kwargs=kwargs,
            future=fut,
            submitted_at=time.perf_counter(),
            priority=priority,
            ttl_seconds=ttl_seconds,
            max_retries=max_retries if max_retries is not None else self.default_max_retries,
        )

        with self._cv:
            if priority == PRIORITY_CRITICAL:
                self._critical_queue.put(req)
            else:
                self._data_queue.put(req)
            self._cv.notify()

        return fut

    def _get_next_request(self) -> Optional[GatewayRequest]:
        """Selecciona la siguiente petición aplicando la política de prioridad y anti-starvation."""
        with self._cv:
            while True:
                if self._shutdown_event.is_set() and self._critical_queue.empty() and self._data_queue.empty():
                    return None

                has_critical = not self._critical_queue.empty()
                has_data = not self._data_queue.empty()

                if not has_critical and not has_data:
                    self._cv.wait(timeout=0.1)
                    continue

                # POLÍTICA ANTI-STARVATION:
                # Si hemos servido N peticiones críticas seguidas y hay peticiones de datos esperando,
                # atendemos obligatoriamente 1 petición de datos para evitar inanición.
                if (
                    self._consecutive_critical_served >= self.max_consecutive_critical
                    and has_data
                ):
                    self._consecutive_critical_served = 0
                    return self._data_queue.get()

                # Prioridad Normal: Atender crítico primero si existe
                if has_critical:
                    self._consecutive_critical_served += 1
                    return self._critical_queue.get()

                # Si no hay críticos, atender datos y reiniciar contador
                if has_data:
                    self._consecutive_critical_served = 0
                    return self._data_queue.get()

    def _process_queue_loop(self) -> None:
        retryable_exceptions = (ConnectionResetError, ConnectionError, BrokenPipeError, BrokerIPCError)

        while True:
            req = self._get_next_request()
            if req is None:
                break

            # 1. Verificación de cancelación cooperativa
            if req.future.cancelled():
                continue

            # 2. Verificación de expiración (TTL) ANTES de tocar el conector MT5
            if req.is_expired():
                req.completed_at = time.perf_counter()
                req.latency_ms = (req.completed_at - req.submitted_at) * 1000
                req.was_discarded_ttl = True
                req.error = "TimeoutError (TTL expired pre-dispatch)"
                req.future.set_exception(
                    TimeoutError(f"Petición {req.req_id} expiró tras {req.latency_ms:.1f}ms en cola (TTL={req.ttl_seconds}s)")
                )
                self.expired_requests_log.append(req.req_id)
                self.completed_requests.append(req)
                continue

            # 3. Ejecución monohilo con reintentos bounded y reconexión controlada
            attempt = 0
            while attempt <= req.max_retries:
                try:
                    result = req.func(*req.args, **req.kwargs)
                    req.completed_at = time.perf_counter()
                    req.latency_ms = (req.completed_at - req.submitted_at) * 1000

                    # Verificación de errores devueltos como retcodes en dict
                    if isinstance(result, dict) and result.get("retcode") is not None:
                        retcode = result["retcode"]
                        if retcode in RETRYABLE_RETCODES:
                            raise BrokerIPCError(f"MT5 transient retcode {retcode}: {RETRYABLE_RETCODES[retcode]}")
                        elif retcode in NON_RETRYABLE_RETCODES:
                            req.error = f"MT5BusinessError_{retcode}: {NON_RETRYABLE_RETCODES.get(retcode, '')}"
                            self.failed_requests_count += 1
                            if not req.future.done():
                                req.future.set_result(result)
                            self.processed_requests_log.append(req.req_id)
                            self.completed_requests.append(req)
                            break

                    if not req.future.done():
                        req.future.set_result(result)
                    self.processed_requests_log.append(req.req_id)
                    self.completed_requests.append(req)
                    break
                except MT5BusinessError as exc:
                    # Errores permanentes de negocio MT5: NUNCA reintentar ni reconectar
                    req.completed_at = time.perf_counter()
                    req.latency_ms = (req.completed_at - req.submitted_at) * 1000
                    req.error = f"MT5BusinessError_{exc.retcode}: {exc.message}"
                    self.failed_requests_count += 1
                    if not req.future.done():
                        req.future.set_exception(exc)
                    self.processed_requests_log.append(req.req_id)
                    self.completed_requests.append(req)
                    break
                except retryable_exceptions as exc:
                    # Fallos IPC / conexión transitorios: Reintentar con backoff y hook de reconexión
                    attempt += 1
                    self.retried_requests_count += 1
                    if attempt > req.max_retries:
                        req.completed_at = time.perf_counter()
                        req.latency_ms = (req.completed_at - req.submitted_at) * 1000
                        req.error = type(exc).__name__
                        self.failed_requests_count += 1
                        if not req.future.done():
                            req.future.set_exception(exc)
                        self.processed_requests_log.append(req.req_id)
                        self.completed_requests.append(req)
                        break
                    # Hook de reconexión simulada
                    if hasattr(self.connector, "reconnect"):
                        self.connector.reconnect()
                    time.sleep(self.retry_backoff_sec * attempt)
                except Exception as exc:
                    # Errores desconocidos: Registrar, propagar limpiamente sin reintentos ni reconexión
                    req.completed_at = time.perf_counter()
                    req.latency_ms = (req.completed_at - req.submitted_at) * 1000
                    req.error = f"UnknownError_{type(exc).__name__}: {str(exc)}"
                    self.failed_requests_count += 1
                    if not req.future.done():
                        req.future.set_exception(exc)
                    self.processed_requests_log.append(req.req_id)
                    self.completed_requests.append(req)
                    break

    def shutdown(self, wait: bool = True, timeout: float = 2.0, cancel_pending: bool = True) -> None:
        self._shutdown_event.set()
        if cancel_pending:
            with self._cv:
                while not self._critical_queue.empty():
                    try:
                        req = self._critical_queue.get_nowait()
                        req.future.cancel()
                    except Exception:
                        pass
                while not self._data_queue.empty():
                    try:
                        req = self._data_queue.get_nowait()
                        req.future.cancel()
                    except Exception:
                        pass
        with self._cv:
            self._cv.notify_all()
        if wait:
            self._worker_thread.join(timeout=timeout)


# ---------------------------------------------------------------------------
# 4. Guardián de Exposición en Vuelo (Simulated Exposure Guard)
# ---------------------------------------------------------------------------

class SimulatedExposureGuard:
    """Guardián de Exposición en Vuelo para el Gateway Concurrente.
    
    Reproduce fielmente la intención de 'strategy/execution/active_position_guard.py':
    1. Regla cardinal: 'Never turn a failed broker request into an empty account'.
       Si el conector no está disponible o falla la consulta, bloquea con BLOCKED_POSITION_STATE_UNAVAILABLE.
    2. Impide órdenes duplicadas en la misma dirección si ya hay una orden en vuelo o posición abierta.
    3. Impide órdenes opuestas en conflicto (hedging no permitido) sobre el mismo activo.
    4. Permite órdenes concurrentes sobre activos distintos sin interferencia.
    5. Libera la reserva atómicamente si la orden falla, expira, es cancelada o es rechazada por el broker.
    """

    def __init__(self, connector: MockMT5Connector):
        self.connector = connector
        self._lock = threading.Lock()
        self._in_flight_orders: Dict[str, Dict[str, Any]] = {}  # symbol -> request

    def check_and_reserve(self, request: Dict[str, Any]) -> Tuple[bool, str, str]:
        symbol = str(request.get("symbol", "UNKNOWN"))
        action = str(request.get("action", "BUY")).upper()

        with self._lock:
            # 0. Verificación de conectividad: jamás asumir cuenta vacía ante desconexión
            if hasattr(self.connector, "is_connected") and not self.connector.is_connected:
                return False, "BLOCKED_POSITION_STATE_UNAVAILABLE", f"Terminal MT5 no conectado o estado no disponible para {symbol}"

            # 1. Verificar si hay posición activa existente en MT5
            if hasattr(self.connector, "get_open_positions"):
                try:
                    positions = self.connector.get_open_positions()
                    if positions is None:
                        return False, "BLOCKED_POSITION_STATE_UNAVAILABLE", f"Estado de posiciones no disponible para {symbol}"
                    if any(p.get("symbol") == symbol for p in positions):
                        return False, "BLOCKED_ACTIVE_TRADE", f"Posicion activa existente en MT5 para {symbol}"
                except Exception as exc:
                    return False, "BLOCKED_POSITION_STATE_UNAVAILABLE", f"Error al consultar posiciones para {symbol}: {exc}"

            # 2. Verificar si hay orden pendiente existente en MT5
            if hasattr(self.connector, "get_pending_orders"):
                try:
                    orders = self.connector.get_pending_orders()
                    if orders is None:
                        return False, "BLOCKED_POSITION_STATE_UNAVAILABLE", f"Estado de ordenes pendientes no disponible para {symbol}"
                    if any(o.get("symbol") == symbol for o in orders):
                        return False, "BLOCKED_PENDING_ORDER", f"Orden pendiente existente en MT5 para {symbol}"
                except Exception as exc:
                    return False, "BLOCKED_POSITION_STATE_UNAVAILABLE", f"Error al consultar ordenes pendientes para {symbol}: {exc}"

            # 3. Verificar si hay orden en vuelo o en cola en el Gateway para este símbolo
            if symbol in self._in_flight_orders:
                existing = self._in_flight_orders[symbol]
                existing_action = existing.get("action", "").upper()
                if existing_action == action:
                    return False, "BLOCKED_IN_FLIGHT_ORDER", f"Orden duplicada {action} en vuelo para {symbol}"
                else:
                    return False, "BLOCKED_CONFLICTING_ORDER", f"Orden opuesta {action} en conflicto con {existing_action} en vuelo para {symbol}"

            # 4. Conceder reserva en vuelo
            self._in_flight_orders[symbol] = dict(request)
            return True, "CLEAR_TO_EXECUTE", f"Reserva en vuelo concedida para {symbol} {action}"

    def release_reservation(
        self,
        symbol: str,
        success: bool = True,
        order_result: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Libera la reserva en vuelo de forma idempotente y actualiza las posiciones del broker si fue exitosa."""
        with self._lock:
            req = self._in_flight_orders.pop(symbol, None)
            if req is None:
                return  # Ya liberada (idempotencia)
            if success and hasattr(self.connector, "add_open_position"):
                ticket = order_result.get("order", 12345) if order_result else 12345
                self.connector.add_open_position({
                    "symbol": symbol,
                    "ticket": ticket,
                    "action": req.get("action", "BUY"),
                    "volume": req.get("volume", 0.01),
                })

    def is_in_flight(self, symbol: str) -> bool:
        with self._lock:
            return symbol in self._in_flight_orders

    def get_in_flight_count(self) -> int:
        with self._lock:
            return len(self._in_flight_orders)

    def clear_all_reservations(self) -> None:
        with self._lock:
            self._in_flight_orders.clear()


# ---------------------------------------------------------------------------
# 5. Proveedor Desacoplado: Gateway Priorizado + Caché Concurrente + Exposure
# ---------------------------------------------------------------------------

@dataclass
class CacheEntry:
    timestamp: float
    data: pd.DataFrame


class DecoupledAsyncMT5Provider:
    """Proveedor que combina caché concurrente con gateway serializado priorizado y guardián de exposición."""

    def __init__(
        self,
        gateway: SerializedMT5Gateway,
        cache_ttl_sec: float = 2.0,
        exposure_guard: Optional[SimulatedExposureGuard] = None,
    ):
        self.gateway = gateway
        self.cache_ttl = cache_ttl_sec
        self.exposure_guard = exposure_guard
        self._cache: Dict[Tuple[str, str, int], CacheEntry] = {}
        self._cache_lock = threading.Lock()

    def get_candles_cached(
        self,
        symbol: str,
        timeframe: str = "M5",
        count: int = 500,
        force_refresh: bool = False,
        timeout: float = 3.0,
        ttl_seconds: Optional[float] = None,
    ) -> pd.DataFrame:
        key = (symbol.upper(), timeframe.upper(), int(count))
        now = time.monotonic()

        # 1. Consulta de caché (Rápida, Concurrente, protegida por lock de memoria)
        if not force_refresh:
            with self._cache_lock:
                entry = self._cache.get(key)
                if entry and (now - entry.timestamp) < self.cache_ttl:
                    return entry.data.copy()

        # 2. Descarga a través del Gateway Serializado con prioridad de datos
        fut = self.gateway.submit(
            self.gateway.connector.copy_rates_from_pos,
            symbol,
            timeframe,
            0,
            count,
            priority=PRIORITY_DATA,
            ttl_seconds=ttl_seconds,
        )
        df = fut.result(timeout=timeout)

        # 3. Guardado seguro en caché
        with self._cache_lock:
            self._cache[key] = CacheEntry(timestamp=time.monotonic(), data=df.copy())

        return df

    def place_order_async(
        self,
        request: Dict[str, Any],
        priority: int = PRIORITY_CRITICAL,
        ttl_seconds: Optional[float] = None,
        bypass_exposure_guard: bool = False,
    ) -> concurrent.futures.Future:
        """Despacha una orden asíncrona retornando un Future y asociando un callback determinista de liberación."""
        symbol = str(request.get("symbol", "UNKNOWN"))

        # 1. Validación previa de exposición atómica
        if self.exposure_guard is not None and not bypass_exposure_guard:
            allowed, status, reason = self.exposure_guard.check_and_reserve(request)
            if not allowed:
                raise ExposureRejectionError(symbol, status, reason)

        # 2. Encolado al Gateway
        fut = self.gateway.submit(
            self.gateway.connector.order_send,
            request,
            priority=priority,
            ttl_seconds=ttl_seconds,
        )

        # 3. Enlace de callback determinista que asegura la liberación bajo CUALQUIER desenlace
        if self.exposure_guard is not None and not bypass_exposure_guard:
            def _on_future_done(f: concurrent.futures.Future) -> None:
                try:
                    if f.cancelled():
                        self.exposure_guard.release_reservation(symbol, success=False)
                        return
                    exc = f.exception()
                    if exc is not None:
                        self.exposure_guard.release_reservation(symbol, success=False)
                        return
                    res = f.result()
                    success = isinstance(res, dict) and res.get("retcode") == 10009
                    self.exposure_guard.release_reservation(
                        symbol,
                        success=success,
                        order_result=res if success else None,
                    )
                except Exception:
                    self.exposure_guard.release_reservation(symbol, success=False)

            fut.add_done_callback(_on_future_done)

        return fut

    def place_order_priority(
        self,
        request: Dict[str, Any],
        timeout: float = 3.0,
        bypass_exposure_guard: bool = False,
    ) -> Dict[str, Any]:
        """Envía una orden prioritaria crítica con validación previa de exposición y espera sincrónica segura."""
        fut = self.place_order_async(
            request,
            priority=PRIORITY_CRITICAL,
            bypass_exposure_guard=bypass_exposure_guard,
        )
        try:
            return fut.result(timeout=timeout)
        except Exception:
            # Si el consumidor sincrónico sufre timeout o interrupción, cancelar cooperativamente
            if not fut.done():
                fut.cancel()
            raise
