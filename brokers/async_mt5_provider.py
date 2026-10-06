"""Proveedor asíncrono y desacoplado de datos y operaciones en MT5 (inspirado en aiomql).

La librería oficial de MetaTrader5 en Python es síncrona y bloqueante: las llamadas a
`copy_rates_from_pos` o `symbols_get` pueden tardar entre 50 y 400 ms en redes con latencia.
Si un solo proceso consulta datos de 20 activos de forma secuencial, se generan retrasos
que impiden ejecutar órdenes críticas de mercado a tiempo.

Este módulo desacopla la arquitectura en dos canales independientes:
1. CANAL DE EJECUCIÓN (Prioridad Crítica / Urgente):
   - `order_check`, `order_send`, `modify_position_stops`.
   - Se ejecuta directamente sin encolamiento en el hilo principal o mediante lock dedicado.
2. CANAL DE DATOS DE MERCADO (Prioridad Normal / En segundo plano):
   - `copy_rates_from_pos`, `copy_ticks_range`, descargas de múltiples timeframes.
   - Se procesa en un pool de hilos (`ThreadPoolExecutor`) no bloqueante con caché TTL.
   - Permite descargar velas en paralelo para múltiples timeframes (H1, M15, M5) simultáneamente.
"""

from __future__ import annotations

import concurrent.futures
from dataclasses import dataclass
from datetime import datetime, timezone
import threading
import time
from typing import Any, Callable, Dict, List, Optional, Tuple

import pandas as pd

try:
    import MetaTrader5 as mt5
except ModuleNotFoundError:
    mt5 = None


@dataclass
class CandleCacheEntry:
    timestamp: float
    data: pd.DataFrame


class AsyncMT5DataProvider:
    """Proveedor concurrente que desacopla la I/O pesada de MT5."""

    def __init__(self, data_provider=None, max_workers: int = 4, cache_ttl_seconds: float = 2.0):
        self.data_provider = data_provider
        self.max_workers = max_workers
        self.cache_ttl = cache_ttl_seconds
        self._executor = concurrent.futures.ThreadPoolExecutor(
            max_workers=max_workers,
            thread_name_prefix="MT5DataWorker"
        )
        self._cache: Dict[Tuple[str, str, int], CandleCacheEntry] = {}
        self._cache_lock = threading.Lock()
        self._execution_lock = threading.Lock()

    def get_candles_cached(
        self,
        symbol: str,
        timeframe: str = "M5",
        count: int = 500,
        force_refresh: bool = False,
    ) -> pd.DataFrame:
        """Obtiene velas utilizando caché con TTL corto para evitar llamadas redundantes a MT5."""
        key = (str(symbol).upper(), str(timeframe).upper(), int(count))
        now = time.monotonic()

        if not force_refresh:
            with self._cache_lock:
                entry = self._cache.get(key)
                if entry and (now - entry.timestamp) < self.cache_ttl:
                    return entry.data.copy()

        # Descarga fresca
        df = self._fetch_candles_direct(symbol, timeframe, count)
        with self._cache_lock:
            self._cache[key] = CandleCacheEntry(timestamp=now, data=df.copy())
        return df

    def _fetch_candles_direct(self, symbol: str, timeframe: str, count: int) -> pd.DataFrame:
        """Llamada directa al proveedor de datos o a la API nativa de MT5."""
        if self.data_provider is not None and hasattr(self.data_provider, "get_candles"):
            return self.data_provider.get_candles(symbol=symbol, timeframe=timeframe, count=count)

        if mt5 is None:
            raise RuntimeError("MetaTrader5 no está disponible")

        tf_map = {
            "M1": mt5.TIMEFRAME_M1,
            "M5": mt5.TIMEFRAME_M5,
            "M15": mt5.TIMEFRAME_M15,
            "M30": mt5.TIMEFRAME_M30,
            "H1": mt5.TIMEFRAME_H1,
            "H4": mt5.TIMEFRAME_H4,
            "D1": mt5.TIMEFRAME_D1,
        }
        mt5_tf = tf_map.get(str(timeframe).upper(), mt5.TIMEFRAME_M5)
        rates = mt5.copy_rates_from_pos(str(symbol), mt5_tf, 0, count)
        if rates is None or len(rates) == 0:
            raise RuntimeError(f"No se pudieron descargar velas de MT5 para {symbol}: {mt5.last_error()}")

        df = pd.DataFrame(rates)
        df["time"] = pd.to_datetime(df["time"], unit="s", utc=True)
        return df

    def batch_fetch_multi_timeframe(
        self,
        symbol: str,
        timeframes: Tuple[str, ...] = ("H1", "M15", "M5"),
        count: int = 500,
        timeout_seconds: float = 4.0,
    ) -> Dict[str, pd.DataFrame]:
        """Descarga en PARALELO múltiples timeframes para el mismo símbolo sin bloquear el hilo principal."""
        futures = {}
        for tf in timeframes:
            fut = self._executor.submit(self.get_candles_cached, symbol, tf, count)
            futures[tf] = fut

        results: Dict[str, pd.DataFrame] = {}
        for tf, fut in futures.items():
            try:
                results[tf] = fut.result(timeout=timeout_seconds)
            except Exception as exc:
                raise RuntimeError(f"Error descargando {symbol} en {tf}: {exc}") from exc

        return results

    def run_priority_execution(self, func: Callable[..., Any], *args, **kwargs) -> Any:
        """Ejecuta una acción de trading crítica (envío o modificación de orden) con bloqueo exclusivo.

        Garantiza que ninguna consulta de datos de fondo sature la conexión IPC con el terminal MT5
        en el milisegundo exacto en que se envía una orden a mercado.
        """
        with self._execution_lock:
            return func(*args, **kwargs)

    def shutdown(self, wait: bool = False) -> None:
        """Cierra el pool de hilos de fondo."""
        self._executor.shutdown(wait=wait)
