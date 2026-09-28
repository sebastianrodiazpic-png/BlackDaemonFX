"""Limitador cooperativo y robusto de solicitudes Deriv entre procesos."""

from __future__ import annotations

import errno
import os
from pathlib import Path
import tempfile
import threading
import time


# Evita que dos hilos del mismo worker intenten adquirir el lock de archivo
# con descriptores distintos. Sin esta capa Windows produjo EACCES y Linux
# EDEADLK bajo la concurrencia scanner + monitor de posiciones.
_PROCESS_LOCK = threading.Lock()


class InterprocessRequestRateLimiter:
    """Espacia solicitudes usando un estado compartido por todos los workers."""

    def __init__(self, path=None, minimum_interval_seconds=None):
        base = Path(os.getenv("LOCALAPPDATA") or tempfile.gettempdir()) / "BlackDaemonFx"
        self.path = Path(
            path
            or os.getenv("DAEMON_DERIV_RATE_LIMIT_STATE_PATH")
            or (base / "market_data" / "deriv_requests.lock")
        )
        self.minimum_interval_seconds = max(
            0.0,
            float(
                minimum_interval_seconds
                if minimum_interval_seconds is not None
                else os.getenv("DAEMON_DERIV_MIN_REQUEST_INTERVAL_SECONDS", "0.20")
            ),
        )
        self.lock_timeout_seconds = max(
            1.0,
            float(os.getenv("DAEMON_DERIV_LOCK_TIMEOUT_SECONDS", "15")),
        )

    @staticmethod
    def _try_lock(handle):
        handle.seek(0)
        if os.name == "nt":
            import msvcrt
            msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
        else:
            import fcntl
            fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)

    @staticmethod
    def _unlock(handle):
        handle.seek(0)
        if os.name == "nt":
            import msvcrt
            msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)
        else:
            import fcntl
            fcntl.flock(handle.fileno(), fcntl.LOCK_UN)

    def _acquire_with_retry(self, handle):
        deadline = time.monotonic() + self.lock_timeout_seconds
        while True:
            try:
                self._try_lock(handle)
                return
            except OSError as exc:
                transient = exc.errno in {
                    errno.EACCES,
                    errno.EAGAIN,
                    errno.EDEADLK,
                    13,
                    35,
                    36,
                }
                if not transient or time.monotonic() >= deadline:
                    raise
                time.sleep(0.02)

    def wait(self):
        if self.minimum_interval_seconds <= 0:
            return 0.0
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with _PROCESS_LOCK:
            with self.path.open("a+b") as handle:
                if handle.tell() == 0:
                    handle.write(b"0")
                    handle.flush()
                self._acquire_with_retry(handle)
                try:
                    handle.seek(0)
                    try:
                        previous = float(
                            handle.read().decode("ascii", errors="ignore") or 0.0
                        )
                    except ValueError:
                        previous = 0.0
                    delay = max(
                        0.0,
                        self.minimum_interval_seconds - (time.time() - previous),
                    )
                    if delay:
                        time.sleep(delay)
                    issued_at = time.time()
                    handle.seek(0)
                    handle.truncate()
                    handle.write(f"{issued_at:.6f}".encode("ascii"))
                    handle.flush()
                    return delay
                finally:
                    self._unlock(handle)


class NoopRequestRateLimiter:
    def wait(self):
        return 0.0
