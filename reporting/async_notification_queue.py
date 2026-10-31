"""Cola de notificaciones, auditoría y exportación asíncrona en segundo plano.

Este módulo desacopla el ciclo principal de trading y análisis de mercado de
las operaciones de entrada/salida (I/O) lentas o bloqueantes, tales como:
1. Escrituras secundarias de eventos de auditoría en la base de datos SQLite.
2. Generación y guardado de archivos Excel (XLSX) en disco mediante openpyxl.
3. Despacho de notificaciones y alertas en consola o canales externos.

Al delegar estas tareas a un hilo de procesamiento en segundo plano con una cola
no bloqueante, el scanner de mercado y el gestor de ejecuciones operan con
latencia mínima y predecible (< 0.05 ms por evento).
"""

from __future__ import annotations

import logging
import os
import queue
import threading
import time
from typing import Any, Callable, Dict, Optional, Tuple


logger = logging.getLogger("AsyncNotificationQueue")


class AsyncNotificationQueue:
    """Gestor de cola asíncrona para tareas de auditoría, reporting y notificaciones."""

    def __init__(
        self,
        maxsize: int = 10000,
        enabled: Optional[bool] = None,
        name: str = "AsyncNotificationWorker",
    ) -> None:
        """Inicializa la cola de notificaciones asíncrona.

        Args:
            maxsize: Capacidad máxima de la cola en memoria.
            enabled: Habilita el despacho asíncrono. Si es False, ejecuta de forma síncrona.
            name: Nombre identificador del hilo de fondo para depuración.
        """
        if enabled is None:
            env_enabled = os.getenv("DAEMONBLACKFX_ASYNC_QUEUE_ENABLED", "1").strip().lower()
            self.enabled = env_enabled not in ("0", "false", "no", "off")
        else:
            self.enabled = bool(enabled)

        self.maxsize = max(100, int(maxsize))
        self.worker_name = str(name)

        self._queue: queue.Queue[Optional[Tuple[Callable, Tuple, Dict]]] = queue.Queue(
            maxsize=self.maxsize
        )
        self._is_running: bool = False
        self._worker_thread: Optional[threading.Thread] = None
        self._state_lock = threading.RLock()

        # Métricas de rendimiento y telemetría
        self._tasks_enqueued: int = 0
        self._tasks_completed: int = 0
        self._tasks_failed: int = 0
        self._tasks_dropped: int = 0
        self._total_processing_time_ms: float = 0.0

        if self.enabled:
            self.start()

    def start(self) -> None:
        """Inicia el hilo de fondo encargado de vaciar la cola de notificaciones."""
        with self._state_lock:
            if self._is_running:
                return

            self._is_running = True
            self._worker_thread = threading.Thread(
                target=self._worker_loop,
                name=self.worker_name,
                daemon=True,
            )
            self._worker_thread.start()

    def _worker_loop(self) -> None:
        """Bucle principal del hilo de fondo que consume y ejecuta tareas encoladas."""
        while self._is_running:
            try:
                item = self._queue.get(timeout=0.25)
            except queue.Empty:
                continue

            if item is None:
                # Centinela de parada recibido
                self._queue.task_done()
                break

            task_callable, args, kwargs = item
            start_time = time.perf_counter()

            try:
                task_callable(*args, **kwargs)
                elapsed_ms = (time.perf_counter() - start_time) * 1000.0
                with self._state_lock:
                    self._tasks_completed += 1
                    self._total_processing_time_ms += elapsed_ms
            except Exception as task_error:
                with self._state_lock:
                    self._tasks_failed += 1
                logger.error(
                    "Error al ejecutar tarea asíncrona en segundo plano: %s",
                    task_error,
                    exc_info=True,
                )
            finally:
                self._queue.task_done()

    def enqueue_task(
        self,
        task_callable: Callable,
        *args: Any,
        **kwargs: Any,
    ) -> bool:
        """Encola una función para su ejecución asíncrona sin bloquear el hilo llamador.

        Args:
            task_callable: Función objetivo a ejecutar.
            *args: Argumentos posicionales.
            **kwargs: Argumentos nombrados.

        Returns:
            True si se encoló o ejecutó satisfactoriamente; False si la cola estaba saturada.
        """
        if not self.enabled:
            # Si el modo asíncrono está desactivado por configuración, ejecutar de inmediato
            try:
                task_callable(*args, **kwargs)
                with self._state_lock:
                    self._tasks_completed += 1
                return True
            except Exception as execution_error:
                with self._state_lock:
                    self._tasks_failed += 1
                logger.error("Error en ejecución síncrona: %s", execution_error)
                return False

        with self._state_lock:
            if not self._is_running:
                self.start()

        item = (task_callable, args, kwargs)
        try:
            self._queue.put_nowait(item)
            with self._state_lock:
                self._tasks_enqueued += 1
            return True
        except queue.Full:
            with self._state_lock:
                self._tasks_dropped += 1
            logger.warning(
                "Cola asíncrona saturada (%d elementos). Se descartó la tarea %s",
                self.maxsize,
                getattr(task_callable, "__name__", str(task_callable)),
            )
            return False

    def enqueue_audit(
        self,
        repository_callable: Callable,
        *args: Any,
        **kwargs: Any,
    ) -> bool:
        """Atajo semántico para encolar escrituras secundarias de auditoría."""
        return self.enqueue_task(repository_callable, *args, **kwargs)

    def enqueue_export(
        self,
        export_callable: Callable,
        *args: Any,
        **kwargs: Any,
    ) -> bool:
        """Atajo semántico para encolar exportaciones de reportes XLSX en segundo plano."""
        return self.enqueue_task(export_callable, *args, **kwargs)

    def flush(self, timeout_seconds: float = 5.0) -> bool:
        """Bloquea hasta que todos los elementos encolados hayan sido procesados.

        Args:
            timeout_seconds: Tiempo máximo de espera en segundos.

        Returns:
            True si la cola se vació por completo; False si se agotó el tiempo de espera.
        """
        deadline = time.monotonic() + max(0.1, float(timeout_seconds))

        while self._queue.unfinished_tasks > 0:
            if time.monotonic() > deadline:
                return False
            time.sleep(0.02)

        return True

    def stop(self, timeout_seconds: float = 3.0) -> None:
        """Detiene el hilo de procesamiento de fondo de forma ordenada."""
        with self._state_lock:
            if not self._is_running:
                return
            self._is_running = False

        try:
            self._queue.put_nowait(None)
        except queue.Full:
            pass

        if self._worker_thread is not None and self._worker_thread.is_alive():
            self._worker_thread.join(timeout=max(0.1, float(timeout_seconds)))

        with self._state_lock:
            self._worker_thread = None

    def get_diagnostics(self) -> Dict[str, Any]:
        """Devuelve un informe de estado y rendimiento de la cola asíncrona."""
        with self._state_lock:
            avg_time = (
                (self._total_processing_time_ms / self._tasks_completed)
                if self._tasks_completed > 0
                else 0.0
            )

            return {
                "enabled": self.enabled,
                "is_running": self._is_running,
                "worker_name": self.worker_name,
                "current_queue_size": self._queue.qsize(),
                "tasks_enqueued": self._tasks_enqueued,
                "tasks_completed": self._tasks_completed,
                "tasks_failed": self._tasks_failed,
                "tasks_dropped": self._tasks_dropped,
                "average_processing_time_ms": round(avg_time, 2),
            }


_GLOBAL_NOTIFICATION_QUEUE: Optional[AsyncNotificationQueue] = None
_GLOBAL_QUEUE_LOCK = threading.RLock()


def get_async_notification_queue() -> AsyncNotificationQueue:
    """Obtiene o crea la instancia global compartida de la cola asíncrona de notificaciones."""
    global _GLOBAL_NOTIFICATION_QUEUE
    with _GLOBAL_QUEUE_LOCK:
        if _GLOBAL_NOTIFICATION_QUEUE is None:
            _GLOBAL_NOTIFICATION_QUEUE = AsyncNotificationQueue()
        return _GLOBAL_NOTIFICATION_QUEUE
