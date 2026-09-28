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

    def _update(self, cooldown=None):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with _PROCESS_LOCK:
            # Lock before any write, including initialization of an empty file.
            # Windows byte locks may cover EOF; initialization outside the lock
            # races with another process and can raise PermissionError.
            with self.path.open("a+b") as handle:
                self._acquire_with_retry(handle)
                try:
                    handle.seek(0)
                    raw = handle.read().decode("ascii")
                    previous = float(raw or 0.0)
                    now = time.time()
                    delay = max(0.0, previous + self.minimum_interval_seconds - now)
                    if cooldown is not None:
                        timestamp = max(previous, now + cooldown - self.minimum_interval_seconds)
                    elif delay:
                        return delay
                    else:
                        timestamp = now
                    handle.seek(0)
                    handle.truncate()
                    handle.write(f"{timestamp:.6f}".encode("ascii"))
                    handle.flush()
                    return 0.0
                finally:
                    self._unlock(handle)

    def defer(self, seconds):
        """Publish a cooldown to every worker, including after the last retry."""
        self._update(cooldown=max(0.0, float(seconds)))

    def wait(self):
        waited = 0.0
        while True:
            delay = self._update()
            if not delay:
                return waited
            # Never sleep holding the process/file lock: other workers must be
            # able to extend a provider cooldown without lock timeouts.
            time.sleep(delay)
            waited += delay


class NoopRequestRateLimiter:
    def wait(self):
        return 0.0
