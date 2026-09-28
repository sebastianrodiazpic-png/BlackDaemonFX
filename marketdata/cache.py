"""Cache TTL acotada para no descargar la misma vela por estrategia."""

from collections import OrderedDict
import threading
import time


class MarketDataCache:
    def __init__(self, max_entries=512):
        self.max_entries = max(1, int(max_entries))
        self._values = OrderedDict()
        self._lock = threading.RLock()

    def get(self, key):
        now = time.monotonic()
        with self._lock:
            item = self._values.get(tuple(key))
            if item is None:
                return None
            expires_at, value = item
            if expires_at <= now:
                self._values.pop(tuple(key), None)
                return None
            self._values.move_to_end(tuple(key))
            return value.copy() if hasattr(value, "copy") else dict(value)

    def put(self, key, value, ttl_seconds):
        with self._lock:
            self._values[tuple(key)] = (
                time.monotonic() + max(0.01, float(ttl_seconds)),
                value.copy() if hasattr(value, "copy") else dict(value),
            )
            self._values.move_to_end(tuple(key))
            while len(self._values) > self.max_entries:
                self._values.popitem(last=False)

    def clear(self):
        with self._lock:
            self._values.clear()
