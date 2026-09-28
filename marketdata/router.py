"""Router Deriv-only: MT5 nunca aporta velas/ticks al análisis primario."""

import threading
import time

from .cache import MarketDataCache


class MarketDataConfigurationError(RuntimeError):
    pass


class DerivOnlyMarketDataRouter:
    source_name = "DERIV_ONLY_ROUTER"

    def __init__(self, *, deriv_provider, metadata_provider=None, cache=None,
                 candle_cache_ttl_seconds=2.0, tick_cache_ttl_seconds=0.5):
        if deriv_provider is None:
            raise MarketDataConfigurationError("Proveedor Deriv no configurado")
        self.deriv_provider = deriv_provider
        self.metadata_provider = metadata_provider
        self.connector = getattr(metadata_provider, "connector", None)
        self.cache = cache or MarketDataCache()
        self.candle_cache_ttl_seconds = max(0.1, float(candle_cache_ttl_seconds))
        self.tick_cache_ttl_seconds = max(0.05, float(tick_cache_ttl_seconds))
        self._inflight = {}
        self._inflight_guard = threading.Lock()
        self._diagnostics = {}

    def connect(self):
        # Deriv se conecta bajo demanda; MT5 sólo conecta para metadatos/ejecución.
        if self.metadata_provider is not None:
            self.metadata_provider.connect()
        return True

    def disconnect(self):
        self.deriv_provider.disconnect()
        self.cache.clear()
        if self.metadata_provider is not None:
            self.metadata_provider.disconnect()

    def resolve_symbol(self, symbol):
        return self.metadata_provider.resolve_symbol(symbol) if self.metadata_provider else str(symbol)

    def ensure_symbol(self, symbol):
        exact = self.metadata_provider.ensure_symbol(symbol) if self.metadata_provider else str(symbol)
        self.deriv_provider.resolve_native_symbol(exact)
        return exact

    def prepare_symbols(self, symbols):
        return [self.ensure_symbol(symbol) for symbol in symbols]

    def search_symbols(self, text):
        return self.metadata_provider.search_symbols(text) if self.metadata_provider else []

    def get_symbol_info(self, symbol):
        if self.metadata_provider:
            return self.metadata_provider.get_symbol_info(symbol)
        return {"name": str(symbol), "visible": True}

    def _lock_for(self, key):
        with self._inflight_guard:
            return self._inflight.setdefault(tuple(key), threading.Lock())

    def get_candles(self, symbol, timeframe="M5", count=1000):
        exact = str(symbol)
        wanted = int(count)
        key = ("candles", exact.casefold(), str(timeframe).upper())
        cached = self.cache.get(key)

        def enough(value):
            return value is not None and (
                len(value) >= wanted
                or int(value.attrs.get("requested_count", 0) or 0) >= wanted
            )

        if enough(cached):
            result = cached.tail(wanted).copy()
            result.attrs["cache_hit"] = True
            return result
        with self._lock_for(key):
            cached = self.cache.get(key)
            if enough(cached):
                result = cached.tail(wanted).copy()
                result.attrs["cache_hit"] = True
                return result
            started = time.perf_counter()
            frame = self.deriv_provider.get_candles(exact, timeframe=timeframe, count=wanted)
            frame.attrs.update({
                "latency_ms": round((time.perf_counter() - started) * 1000, 3),
                "cache_hit": False,
                "requested_count": wanted,
            })
            closed = frame[frame["complete"].astype(bool)]
            self._diagnostics[exact.casefold()] = {
                "source": frame.attrs.get("market_data_source"),
                "execution_symbol": exact,
                "native_symbol": frame.attrs.get("native_symbol"),
                "timeframe": str(timeframe).upper(),
                "rows": len(frame),
                "latest_candle_time": frame.iloc[-1]["time"].isoformat(),
                "latest_closed_candle_time": (
                    closed.iloc[-1]["time"].isoformat() if not closed.empty else None
                ),
                "volume_reliable": bool(frame.attrs.get("volume_reliable")),
                "latency_ms": frame.attrs["latency_ms"],
                "cache_hit": False,
            }
            self.cache.put(key, frame, self.candle_cache_ttl_seconds)
            return frame.tail(wanted).copy()

    def get_current_tick(self, symbol):
        exact = str(symbol)
        key = ("tick", exact.casefold())
        cached = self.cache.get(key)
        if cached is not None:
            cached["cache_hit"] = True
            return cached
        with self._lock_for(key):
            cached = self.cache.get(key)
            if cached is not None:
                cached["cache_hit"] = True
                return cached
            started = time.perf_counter()
            tick = self.deriv_provider.get_current_tick(exact)
            tick.update({
                "latency_ms": round((time.perf_counter() - started) * 1000, 3),
                "cache_hit": False,
            })
            diagnostic = dict(self._diagnostics.get(exact.casefold()) or {})
            diagnostic.update({
                "source": tick.get("source"),
                "execution_symbol": exact,
                "native_symbol": tick.get("native_symbol"),
                "latest_tick_time": str(tick.get("time")),
                "tick_latency_ms": tick["latency_ms"],
            })
            self._diagnostics[exact.casefold()] = diagnostic
            self.cache.put(key, tick, self.tick_cache_ttl_seconds)
            return dict(tick)

    def diagnostics(self, symbol):
        return dict(self._diagnostics.get(str(symbol).casefold()) or {})

    def active_symbols(self):
        return self.deriv_provider.active_symbols()
