"""Feed Deriv Charts/API para sintéticos, Forex, metales e índices."""

from __future__ import annotations

import json
import os
import random
import re
import threading
import time

import pandas as pd

from .normalization import (
    MarketDataIdentity,
    MarketDataValidationError,
    normalize_candles,
    normalize_tick,
    timeframe_seconds,
)
from .rate_limit import InterprocessRequestRateLimiter, NoopRequestRateLimiter


class DerivAPIError(RuntimeError):
    pass


class DerivWebSocketTransport:
    def __init__(self, endpoint, timeout_seconds=12.0):
        self.endpoint = str(endpoint)
        self.timeout_seconds = float(timeout_seconds)
        self._socket = None
        self._lock = threading.RLock()
        self._request_id = 0

    def connect(self):
        with self._lock:
            if self._socket is not None:
                return True
            try:
                import websocket
            except ImportError as exc:
                raise DerivAPIError(
                    "Falta websocket-client. Ejecute: python -m pip install -r requirements.txt"
                ) from exc
            self._socket = websocket.create_connection(
                self.endpoint, timeout=self.timeout_seconds, enable_multithread=True,
            )
            return True

    def disconnect(self):
        with self._lock:
            socket, self._socket = self._socket, None
            if socket is not None:
                try:
                    socket.close()
                except Exception:
                    pass

    def request(self, payload):
        with self._lock:
            last_error = None
            for _attempt in range(2):
                try:
                    self.connect()
                    self._request_id += 1
                    request_id = self._request_id
                    message = dict(payload)
                    message["req_id"] = request_id
                    self._socket.settimeout(self.timeout_seconds)
                    self._socket.send(json.dumps(message, separators=(",", ":")))
                    deadline = time.monotonic() + self.timeout_seconds
                    while True:
                        remaining = deadline - time.monotonic()
                        if remaining <= 0:
                            raise TimeoutError("Deriv response deadline exceeded")
                        self._socket.settimeout(remaining)
                        response = json.loads(self._socket.recv())
                        if int(response.get("req_id") or -1) == request_id:
                            return response
                except Exception as exc:
                    last_error = exc
                    self.disconnect()
                    if _attempt == 0:
                        time.sleep(0.5 + random.uniform(0.0, 0.5))
            raise DerivAPIError(f"Deriv WebSocket no respondió: {last_error}")


class DerivMarketDataProvider:
    source_name = "DERIV_CHARTS_WEBSOCKET"

    _SEMANTIC_ALIASES = {
        "xauusd": {"xauusd", "gold", "goldusd"},
        "xagusd": {"xagusd", "silver", "silverusd"},
        "wallstreet30": {"wallstreet30", "us30", "dowjones", "dowjones30"},
        "ustech100": {"ustech100", "nasdaq", "nasdaq100", "us100"},
        "us500": {"us500", "ussp500", "sp500", "spx500", "sandp500"},
    }

    def __init__(self, *, endpoint=None, symbol_map=None, transport=None, rate_limiter=None):
        self.endpoint = endpoint or "wss://api.derivws.com/trading/v1/options/ws/public"
        self.transport = transport or DerivWebSocketTransport(self.endpoint)
        self.rate_limiter = rate_limiter or (
            NoopRequestRateLimiter()
            if transport is not None
            else InterprocessRequestRateLimiter()
        )
        self.symbol_map = {str(k).casefold(): str(v) for k, v in (symbol_map or {}).items()}
        self._active_symbols = None

    def connect(self):
        return self.transport.connect()

    def disconnect(self):
        return self.transport.disconnect()

    @staticmethod
    def _normalized_name(value):
        normalized = "".join(ch for ch in str(value).casefold() if ch.isalnum())
        for suffix in ("micro", "mini", "pro", "raw"):
            if normalized.endswith(suffix):
                normalized = normalized[:-len(suffix)]
        return normalized

    @classmethod
    def _requested_aliases(cls, value):
        normalized = cls._normalized_name(value)
        aliases = {normalized}
        for canonical, values in cls._SEMANTIC_ALIASES.items():
            if normalized == canonical or normalized in values:
                aliases.update(values)
        return {alias for alias in aliases if alias}

    @classmethod
    def _row_aliases(cls, row):
        aliases = set()
        # El endpoint publico nuevo usa underlying_symbol_name y
        # underlying_symbol. Conservamos los nombres del contrato legado para
        # que instalaciones/proxies anteriores sigan siendo compatibles.
        for field in (
            "display_name",
            "market_display_name",
            "symbol",
            "underlying_symbol",
            "underlying_symbol_name",
        ):
            value = cls._normalized_name(row.get(field) or "")
            if not value:
                continue
            aliases.add(value)
            for prefix in ("frx", "otc", "cry"):
                if value.startswith(prefix) and len(value) > len(prefix):
                    aliases.add(value[len(prefix):])
        expanded = set(aliases)
        for canonical, values in cls._SEMANTIC_ALIASES.items():
            if aliases.intersection(values | {canonical}):
                expanded.update(values)
                expanded.add(canonical)
        return expanded

    def _load_active_symbols(self, force=False):
        if self._active_symbols is None or force:
            # El endpoint publico trading/v1/options/ws/public valida el
            # contrato de cada mensaje estrictamente. ``product_type`` era un
            # filtro del contrato WebSocket legado y provoca:
            # "Input validation failed: Properties not allowed: product_type".
            # La respuesta sin ese filtro ya contiene el catalogo que
            # necesitamos y el matching posterior selecciona el instrumento.
            response = self._request({"active_symbols": "brief"})
            rows = list(response.get("active_symbols") or [])
            if not rows:
                raise DerivAPIError("Deriv no devolvió instrumentos en active_symbols")
            self._active_symbols = rows
        return self._active_symbols

    @staticmethod
    def _api_error_message(response):
        error = response.get("error") if isinstance(response, dict) else None
        if not error:
            return None
        if isinstance(error, dict):
            return str(error.get("message") or error)
        return str(error)

    @staticmethod
    def _is_rate_limit_error(message):
        value = str(message or "").casefold()
        return "rate limit" in value or "too many request" in value

    def _request(self, payload):
        """Ejecuta una solicitud pública con pacing y reintento acotado."""
        retries = max(0, int(os.getenv("DAEMON_DERIV_RATE_LIMIT_RETRIES", "4")))
        base_delay = max(0.05, float(os.getenv("DAEMON_DERIV_RATE_LIMIT_BACKOFF_SECONDS", "3.0")))
        last_message = None
        for attempt in range(retries + 1):
            self.rate_limiter.wait()
            try:
                response = self.transport.request(payload)
            except (DerivAPIError, OSError, TimeoutError):
                # Coordinate recovery across workers without serving stale candles.
                defer = getattr(self.rate_limiter, "defer", None)
                if callable(defer):
                    defer(base_delay + random.uniform(0.0, 0.5))
                raise
            last_message = self._api_error_message(response)
            if not last_message:
                return response
            if not self._is_rate_limit_error(last_message):
                raise DerivAPIError(last_message)
            delay = min(30.0, base_delay * (2 ** attempt))
            delay += random.uniform(0.0, min(0.25, delay * 0.20))
            defer = getattr(self.rate_limiter, "defer", None)
            if callable(defer):
                defer(delay)
            if attempt >= retries:
                raise DerivAPIError(last_message)
            if not callable(defer):
                time.sleep(delay)
        raise DerivAPIError(str(last_message or "Error desconocido de Deriv"))

    def active_symbols(self):
        return [dict(row) for row in self._load_active_symbols()]

    def resolve_native_symbol(self, execution_symbol):
        requested = str(execution_symbol).strip()
        explicit = self.symbol_map.get(requested.casefold())
        if explicit:
            return explicit
        requested_aliases = self._requested_aliases(requested)
        matches = []
        for row in self._load_active_symbols():
            native = row.get("symbol") or row.get("underlying_symbol")
            if native and requested_aliases.intersection(self._row_aliases(row)):
                matches.append(str(native))
        matches = sorted(set(matches))
        if len(matches) == 1:
            self.symbol_map[requested.casefold()] = matches[0]
            return matches[0]
        if not matches:
            raise MarketDataValidationError(
                f"Deriv Charts no ofrece un equivalente para '{requested}'."
            )
        raise MarketDataValidationError(
            f"Mapeo Deriv ambiguo para '{requested}': {matches}. "
            "Defínalo en DAEMON_DERIV_SYMBOL_MAP_JSON."
        )

    def get_candles(self, execution_symbol, timeframe="M5", count=1000):
        native = self.resolve_native_symbol(execution_symbol)
        granularity = timeframe_seconds(timeframe)
        response = self._request({
            "ticks_history": native,
            "adjust_start_time": 1,
            "count": min(5000, max(3, int(count))),
            "end": "latest",
            "style": "candles",
            "granularity": granularity,
        })
        rows = []
        now_epoch = int(time.time())
        for candle in response.get("candles") or []:
            epoch = int(candle.get("epoch") or 0)
            rows.append({
                "time": pd.to_datetime(epoch, unit="s", utc=True),
                "open": candle.get("open"),
                "high": candle.get("high"),
                "low": candle.get("low"),
                "close": candle.get("close"),
                "tick_volume": candle.get("tick_count", 0),
                "real_volume": 0,
                "spread": 0,
                "complete": bool(epoch > 0 and epoch + granularity <= now_epoch),
            })
        return normalize_candles(
            rows,
            identity=MarketDataIdentity(str(execution_symbol), native, self.source_name),
            timeframe=timeframe,
        )

    def get_current_tick(self, execution_symbol):
        native = self.resolve_native_symbol(execution_symbol)
        response = self._request({
            "ticks_history": native, "count": 1, "end": "latest", "style": "ticks",
        })
        history = response.get("history") or {}
        prices = list(history.get("prices") or [])
        times = list(history.get("times") or [])
        if not prices:
            raise DerivAPIError(f"Deriv no devolvió ticks para {native}")
        price = prices[-1]
        return normalize_tick({
            "last": price,
            "bid": price,
            "ask": price,
            "time": pd.to_datetime(times[-1], unit="s", utc=True)
            if times else pd.Timestamp.now(tz="UTC"),
        }, identity=MarketDataIdentity(str(execution_symbol), native, self.source_name))
