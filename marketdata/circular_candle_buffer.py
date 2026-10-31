"""Búfer circular y caché en memoria para series temporales de velas (M1, M5, M15, H1).

Este módulo implementa una estructura de datos de búfer circular con tamaño
fijo (por defecto 300 velas por par símbolo-temporalidad).

Beneficios de arquitectura informática:
1. Evita la recolección repetitiva de basura (Garbage Collection) en Python
   al no re-instanciar DataFrames completos en cada iteración de escaneo.
2. Reduce la latencia de análisis sirviendo datos frescos directamente desde
   memoria durante la vigencia de la vela en formación.
3. Acota el consumo de memoria RAM a un tamaño predecible y constante mediante
   recorte FIFO garantizado.
"""

from __future__ import annotations

import os
import threading
import time
from typing import Any, Callable, Dict, Optional, Tuple
import pandas as pd


DEFAULT_BUFFER_SIZE: int = 300
DEFAULT_CACHE_TTL_SECONDS: float = 2.5


class CircularCandleBuffer:
    """Búfer circular acotado en memoria para velas de mercado por símbolo y temporalidad."""

    def __init__(
        self,
        max_candles: int = DEFAULT_BUFFER_SIZE,
        ttl_seconds: float = DEFAULT_CACHE_TTL_SECONDS,
        enabled: Optional[bool] = None,
    ) -> None:
        """Inicializa el búfer circular de velas.

        Args:
            max_candles: Número máximo de velas retenidas por símbolo y temporalidad.
            ttl_seconds: Tiempo en segundos durante el cual el búfer se considera fresco.
            enabled: Habilita o deshabilita el almacenamiento en caché en memoria.
        """
        env_size_str = os.getenv("DAEMONBLACKFX_CANDLE_BUFFER_SIZE", str(max_candles))
        try:
            self.max_candles = max(10, int(env_size_str))
        except ValueError:
            self.max_candles = max_candles

        env_ttl_str = os.getenv("DAEMONBLACKFX_CANDLE_BUFFER_TTL", str(ttl_seconds))
        try:
            self.ttl_seconds = max(0.1, float(env_ttl_str))
        except ValueError:
            self.ttl_seconds = ttl_seconds

        if enabled is None:
            env_enabled = os.getenv("DAEMONBLACKFX_CANDLE_BUFFER_ENABLED", "1").strip().lower()
            self.enabled = env_enabled not in ("0", "false", "no", "off")
        else:
            self.enabled = bool(enabled)

        # Estructura principal de almacenamiento: (symbol, timeframe) -> DataFrame
        self._buffer: Dict[Tuple[str, str], pd.DataFrame] = {}
        self._last_updated: Dict[Tuple[str, str], float] = {}

        # Bloqueos de concurrencia reentrantes para acceso multi-hilo seguro
        self._global_lock = threading.RLock()
        self._series_locks: Dict[Tuple[str, str], threading.RLock] = {}

        # Métricas de telemetría y diagnóstico
        self._cache_hits: int = 0
        self._cache_misses: int = 0
        self._updates_count: int = 0

    def _get_series_lock(self, key: Tuple[str, str]) -> threading.RLock:
        """Obtiene o crea un cerrojo reentrante para un activo y marco temporal específico."""
        with self._global_lock:
            if key not in self._series_locks:
                self._series_locks[key] = threading.RLock()
            return self._series_locks[key]

    def _normalize_key(self, symbol: str, timeframe: str) -> Tuple[str, str]:
        """Normaliza el par símbolo y temporalidad a mayúsculas consistentes."""
        return (str(symbol).strip().upper(), str(timeframe).strip().upper())

    def get(self, symbol: str, timeframe: str, count: int) -> Optional[pd.DataFrame]:
        """Obtiene velas desde el búfer circular si están presentes y frescas.

        Args:
            symbol: Identificador del instrumento financiero.
            timeframe: Marco temporal de las velas (e.g., 'M1', 'M5', 'M15', 'H1').
            count: Cantidad requerida de velas recientes.

        Returns:
            DataFrame con las últimas `count` velas si están disponibles y vigentes,
            o `None` si expiró el tiempo de vida o no existen datos suficientes.
        """
        if not self.enabled:
            return None

        key = self._normalize_key(symbol, timeframe)
        current_time = time.monotonic()

        with self._global_lock:
            cached_frame = self._buffer.get(key)
            last_timestamp = self._last_updated.get(key, 0.0)

            if cached_frame is None:
                return None

            is_fresh = (current_time - last_timestamp) <= self.ttl_seconds
            has_enough_bars = len(cached_frame) >= int(count)

            if is_fresh and has_enough_bars:
                self._cache_hits += 1
                result_frame = cached_frame.tail(int(count)).copy()
                result_frame.attrs["buffer_hit"] = True
                return result_frame

        return None

    def put(self, symbol: str, timeframe: str, candles_frame: pd.DataFrame) -> pd.DataFrame:
        """Incorpora nuevas velas al búfer circular, recortando al tamaño máximo configurado.

        Args:
            symbol: Identificador del instrumento financiero.
            timeframe: Marco temporal de las velas.
            candles_frame: DataFrame con velas entrantes.

        Returns:
            DataFrame normalizado y acotado a `max_candles`.
        """
        if not self.enabled or candles_frame is None or candles_frame.empty:
            return candles_frame

        key = self._normalize_key(symbol, timeframe)
        series_lock = self._get_series_lock(key)

        with series_lock:
            clean_frame = candles_frame.copy()

            # Asegurar orden cronológico ascendente si existe columna 'time'
            if "time" in clean_frame.columns:
                clean_frame = clean_frame.sort_values("time").reset_index(drop=True)

            # Acotar el DataFrame al tamaño máximo fijo del búfer circular (FIFO)
            if len(clean_frame) > self.max_candles:
                clean_frame = clean_frame.tail(self.max_candles).reset_index(drop=True)

            with self._global_lock:
                self._buffer[key] = clean_frame
                self._last_updated[key] = time.monotonic()
                self._updates_count += 1

            return clean_frame

    def get_or_fetch(
        self,
        symbol: str,
        timeframe: str,
        count: int,
        fetch_callable: Callable[[], pd.DataFrame],
    ) -> pd.DataFrame:
        """Obtiene las velas desde la caché o las recupera mediante la función provista.

        Args:
            symbol: Identificador del instrumento.
            timeframe: Marco temporal.
            count: Cantidad requerida de velas.
            fetch_callable: Función para obtener las velas si no están en memoria.

        Returns:
            DataFrame con las velas requeridas.
        """
        if not self.enabled:
            return fetch_callable()

        cached_frame = self.get(symbol=symbol, timeframe=timeframe, count=count)
        if cached_frame is not None:
            return cached_frame

        key = self._normalize_key(symbol, timeframe)
        series_lock = self._get_series_lock(key)

        with series_lock:
            # Doble comprobación con cerrojo adquirido
            cached_frame_locked = self.get(symbol=symbol, timeframe=timeframe, count=count)
            if cached_frame_locked is not None:
                return cached_frame_locked

            with self._global_lock:
                self._cache_misses += 1

            fresh_frame = fetch_callable()
            stored_frame = self.put(symbol=symbol, timeframe=timeframe, candles_frame=fresh_frame)

            requested_count = min(int(count), len(stored_frame))
            result = stored_frame.tail(requested_count).copy()
            result.attrs["buffer_hit"] = False
            return result

    def clear(self) -> None:
        """Limpia todo el contenido del búfer circular y reinicia estadísticas."""
        with self._global_lock:
            self._buffer.clear()
            self._last_updated.clear()
            self._series_locks.clear()
            self._cache_hits = 0
            self._cache_misses = 0
            self._updates_count = 0

    def get_diagnostics(self) -> Dict[str, Any]:
        """Devuelve métricas detalladas de funcionamiento y rendimiento del búfer."""
        with self._global_lock:
            total_requests = self._cache_hits + self._cache_misses
            hit_ratio = (self._cache_hits / total_requests) if total_requests > 0 else 0.0

            series_detail = []
            for (sym, tf), frame in self._buffer.items():
                series_detail.append({
                    "symbol": sym,
                    "timeframe": tf,
                    "candles_count": len(frame),
                })

            return {
                "enabled": self.enabled,
                "max_candles_per_series": self.max_candles,
                "ttl_seconds": self.ttl_seconds,
                "total_tracked_series": len(self._buffer),
                "cache_hits": self._cache_hits,
                "cache_misses": self._cache_misses,
                "hit_ratio_percent": round(hit_ratio * 100.0, 2),
                "updates_count": self._updates_count,
                "series": series_detail,
            }


class BufferedCandleProvider:
    """Envoltura de proveedor de mercado que delega lecturas de velas al búfer circular."""

    def __init__(
        self,
        base_provider: Any,
        candle_buffer: Optional[CircularCandleBuffer] = None,
    ) -> None:
        """Inicializa la envoltura de proveedor con búfer circular.

        Args:
            base_provider: Proveedor subyacente de datos de mercado (MT5 o Deriv).
            candle_buffer: Instancia del búfer circular. Si es None, se crea una nueva.
        """
        self.base_provider = base_provider
        self.candle_buffer = candle_buffer or CircularCandleBuffer()

    def get_candles(
        self,
        symbol: str,
        timeframe: str = "M5",
        count: int = 1000,
    ) -> pd.DataFrame:
        """Obtiene velas utilizando el búfer circular en memoria para evitar I/O repetitivo.

        Args:
            symbol: Identificador del símbolo.
            timeframe: Marco temporal (M1, M5, M15, H1, etc.).
            count: Cantidad requerida de velas.

        Returns:
            DataFrame con las velas ordenadas cronológicamente.
        """
        def fetch_from_underlying() -> pd.DataFrame:
            return self.base_provider.get_candles(
                symbol=symbol,
                timeframe=timeframe,
                count=count,
            )

        return self.candle_buffer.get_or_fetch(
            symbol=symbol,
            timeframe=timeframe,
            count=count,
            fetch_callable=fetch_from_underlying,
        )

    def get_last_closed_candle(self, symbol: str, timeframe: str = "M5") -> pd.Series:
        """Obtiene la última vela cerrada delegando en get_candles con búfer."""
        candles = self.get_candles(symbol=symbol, timeframe=timeframe, count=3)
        if len(candles) < 2:
            raise RuntimeError(
                f"No hay suficientes velas en el búfer para '{symbol}' ({timeframe})"
            )
        return candles.iloc[-2].copy()

    def __getattr__(self, attribute_name: str) -> Any:
        """Delega cualquier otro método o propiedad no interceptado al proveedor base."""
        return getattr(self.base_provider, attribute_name)
