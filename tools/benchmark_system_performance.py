"""tools/benchmark_system_performance.py - Arnés de Benchmarking y Profiling Integral.

Ejecuta una batería completa de pruebas de rendimiento sin alterar datos operativos:
1. Rendimiento de Base de Datos (I/O, Queries frecuentes, Transacciones, PRAGMAs y WAL Checkpoints).
2. Capa de Datos de Mercado (Caché de velas, Conversión Zero-Copy, Monotonía y RingBuffer).
3. Motores de Estrategia (MultiTimeframe SMC, Malaysian SNR y New York ORB).
4. Profiling de Memoria y Presión del Recolector de Basura (tracemalloc, gc stats).
"""

from __future__ import annotations

import sys
if sys.path and ("tools" in sys.path[0] or sys.path[0].endswith("tools")):
    sys.path.pop(0)
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import gc
import json
import os
import tempfile
import time
import tracemalloc
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List

import numpy as np
import pandas as pd

# Fijar base de datos para benchmarking local seguro
workspace_db = PROJECT_ROOT / "storage" / "trading_bot.sqlite3"
os.environ["DAEMONBLACKFX_DB_PATH"] = str(workspace_db)

from database.database import get_engine, resolve_db_path
from database.repository import TradingRepository
from marketdata.circular_candle_buffer import CircularCandleBuffer
from strategy.execution.multi_timeframe import MultiTimeframeAnalyzer, MultiTimeframeConfig
from strategy.execution.trade_pipeline import PipelineConfig
from strategy.malaysian_snr.malaysian_snr_strategy import MalaysianSNRStrategy
from strategy.orb.new_york_orb import NewYorkORBStrategy, ORBConfig


@dataclass
class BenchmarkMetric:
    name: str
    category: str
    iterations: int
    total_time_ms: float
    avg_time_ms: float
    p95_time_ms: float
    p99_time_ms: float
    min_time_ms: float
    max_time_ms: float
    status: str = "OPTIMAL"  # OPTIMAL (<5ms), ACCEPTABLE (5-50ms), BOTTLENECK (>50ms)
    details: Dict[str, Any] = field(default_factory=dict)


def time_block(func: Callable, iterations: int = 10, *args, **kwargs) -> tuple[List[float], Any]:
    """Mide la latencia por iteración en milisegundos."""
    times = []
    result = None
    for _ in range(iterations):
        t0 = time.perf_counter()
        result = func(*args, **kwargs)
        t1 = time.perf_counter()
        times.append((t1 - t0) * 1000.0)
    return times, result


def compute_metrics(name: str, category: str, times: List[float], details: Dict[str, Any] | None = None) -> BenchmarkMetric:
    arr = np.array(times)
    avg_ms = float(np.mean(arr))
    p95_ms = float(np.percentile(arr, 95))
    p99_ms = float(np.percentile(arr, 99))
    min_ms = float(np.min(arr))
    max_ms = float(np.max(arr))
    total_ms = float(np.sum(arr))

    if avg_ms < 5.0:
        status = "OPTIMAL"
    elif avg_ms < 50.0:
        status = "ACCEPTABLE"
    else:
        status = "BOTTLENECK"

    return BenchmarkMetric(
        name=name,
        category=category,
        iterations=len(times),
        total_time_ms=total_ms,
        avg_time_ms=avg_ms,
        p95_time_ms=p95_ms,
        p99_time_ms=p99_ms,
        min_time_ms=min_ms,
        max_time_ms=max_ms,
        status=status,
        details=details or {},
    )


class MockMarketDataProvider:
    """Proveedor determinista de velas sintéticas para benchmarks sin requerir MT5 abierto."""

    def __init__(self):
        self.symbols = ["Volatility 75 Index", "Step Index", "US Tech 100", "EURUSD", "Boom 1000 Index"]
        self._cache = {}

    def get_candles(self, symbol: str, timeframe: str = "M5", count: int = 500) -> pd.DataFrame:
        key = (symbol, timeframe, count)
        if key in self._cache:
            return self._cache[key].copy()

        freq_map = {"M1": "1min", "M5": "5min", "M15": "15min", "H1": "1h", "H4": "4h", "D1": "1D"}
        freq = freq_map.get(timeframe, "5min")
        dates = pd.date_range("2026-11-01 00:00:00", periods=count, freq=freq, tz="UTC")

        # Generar serie de precios realista (Random Walk con tendencia)
        np.random.seed(42 + hash(symbol) % 1000)
        returns = np.random.normal(0.0001, 0.002, count)
        price = 1000.0 * np.exp(np.cumsum(returns))
        high = price * (1.0 + np.abs(np.random.normal(0.0, 0.001, count)))
        low = price * (1.0 - np.abs(np.random.normal(0.0, 0.001, count)))
        open_ = (high + low) / 2.0 + np.random.normal(0.0, 0.1, count)
        volume = np.random.randint(100, 5000, count)

        df = pd.DataFrame({
            "time": dates,
            "open": open_,
            "high": high,
            "low": low,
            "close": price,
            "tick_volume": volume,
            "spread": np.ones(count, dtype=int) * 2,
            "real_volume": volume,
        })
        self._cache[key] = df
        return df.copy()

    def get_current_tick(self, symbol: str) -> dict:
        return {"bid": 1000.0, "ask": 1000.2, "spread": 2, "time": time.time()}


def benchmark_sqlite_and_repository(repo: TradingRepository) -> List[BenchmarkMetric]:
    """Evalúa la latencia de queries, PRAGMAs y transacciones en SQLite."""
    metrics = []

    # 1. Diagnóstico de PRAGMAs en la base en uso
    with repo.Session() as session:
        conn = session.connection()
        journal_mode = conn.exec_driver_sql("PRAGMA journal_mode;").scalar()
        synchronous = conn.exec_driver_sql("PRAGMA synchronous;").scalar()
        mmap_size = conn.exec_driver_sql("PRAGMA mmap_size;").scalar()
        cache_size = conn.exec_driver_sql("PRAGMA cache_size;").scalar()
        busy_timeout = conn.exec_driver_sql("PRAGMA busy_timeout;").scalar()

    pragma_details = {
        "journal_mode": journal_mode,
        "synchronous": synchronous,
        "mmap_size_mb": (mmap_size or 0) / (1024 * 1024),
        "cache_size_kb": abs(cache_size or 0),
        "busy_timeout_ms": busy_timeout,
    }

    # 2. Benchmark de lecturas frecuentes
    t_open, _ = time_block(lambda: repo.open_trades(source="DEMO"), iterations=30)
    metrics.append(compute_metrics("Repository: open_trades()", "Database I/O", t_open, pragma_details))

    t_worker, _ = time_block(lambda: repo.worker_runtime_states(source="DEMO"), iterations=30)
    metrics.append(compute_metrics("Repository: worker_runtime_states()", "Database I/O", t_worker))

    t_latest_res, _ = time_block(lambda: repo.latest_symbol_process_result("Step Index", source="DEMO"), iterations=30)
    metrics.append(compute_metrics("Repository: latest_symbol_process_result()", "Database I/O", t_latest_res))

    t_trades_df, _ = time_block(lambda: repo.trades_dataframe(source="DEMO"), iterations=15)
    metrics.append(compute_metrics("Repository: trades_dataframe()", "Database I/O", t_trades_df))

    t_acc_df, _ = time_block(lambda: repo.account_trade_history_dataframe(source="DEMO"), iterations=15)
    metrics.append(compute_metrics("Repository: account_trade_history_dataframe()", "Database I/O", t_acc_df))

    # 3. Checkpoint WAL
    t_chkpt, res = time_block(lambda: repo.checkpoint_database(mode="PASSIVE"), iterations=5)
    metrics.append(compute_metrics("SQLite: PRAGMA wal_checkpoint(PASSIVE)", "Database I/O", t_chkpt, details={"res": res}))

    # 4. Transacciones de escritura aisladas (en base temporal dedicada)
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmp_dir:
        tmp_db_path = Path(tmp_dir) / "bench_test.sqlite3"
        tmp_repo = TradingRepository(tmp_db_path)
        try:
            def write_100_signals_individual():
                now = pd.Timestamp.now(tz="UTC")
                for i in range(100):
                    sig = {
                        "instrument": f"BENCH_SYM_{i % 5}",
                        "signal_time": now,
                        "timeframe": "M5",
                        "direction": "BUY",
                        "strategy_name": "BENCH_STRATEGY",
                        "status": "DETECTED",
                        "entry_price": 100.0 + i,
                        "stop_loss": 90.0,
                        "take_profit": 120.0,
                    }
                    tmp_repo.save_signal(sig)

            def write_100_signals_batch():
                now = pd.Timestamp.now(tz="UTC")
                batch = [
                    {
                        "instrument": f"BENCH_SYM_{i % 5}",
                        "signal_time": now,
                        "timeframe": "M5",
                        "direction": "BUY",
                        "strategy_name": "BENCH_STRATEGY",
                        "status": "DETECTED",
                        "entry_price": 100.0 + i,
                        "stop_loss": 90.0,
                        "take_profit": 120.0,
                    }
                    for i in range(100)
                ]
                tmp_repo.save_signals_batch(batch)

            t_indiv, _ = time_block(write_100_signals_individual, iterations=5)
            metrics.append(compute_metrics("SQLite Individual Writes (100 signals)", "Database Write", t_indiv))

            t_batch, _ = time_block(write_100_signals_batch, iterations=20)
            metrics.append(compute_metrics("SQLite Batch Write (100 signals)", "Database Write", t_batch))
        finally:
            try:
                tmp_repo.Session.kw["bind"].dispose()
            except Exception:
                pass

    return metrics


def benchmark_candle_data_layer(provider: MockMarketDataProvider) -> List[BenchmarkMetric]:
    """Evalúa la velocidad de entrega de velas, copias y buffers."""
    metrics = []

    # 1. Obtención de velas (500 velas M5)
    t_candles, _ = time_block(lambda: provider.get_candles("Volatility 75 Index", "M5", 500), iterations=100)
    metrics.append(compute_metrics("Candle Delivery (500 M5 bars)", "Market Data Layer", t_candles))

    # 2. Overhead de slicing .copy() vs zero-copy view
    df = provider.get_candles("Volatility 75 Index", "M5", 1000)
    t_copy, _ = time_block(lambda: df.iloc[-500:].reset_index(drop=True).copy(), iterations=200)
    metrics.append(compute_metrics("DataFrame iloc[-500:].reset_index().copy()", "Memory / CPU", t_copy))

    t_view, _ = time_block(lambda: df.iloc[-500:], iterations=200)
    metrics.append(compute_metrics("DataFrame iloc[-500:] (Zero-Copy View)", "Memory / CPU", t_view))

    # 3. Buffer circular (RingBuffer O(1) Candle Storage)
    buffer = CircularCandleBuffer(max_candles=500, ttl_seconds=10.0)
    t_ring_put, _ = time_block(lambda: buffer.put("Volatility 75 Index", "M5", df), iterations=100)
    metrics.append(compute_metrics("CircularCandleBuffer (put 500 candles)", "Market Data Layer", t_ring_put))

    t_ring_get, _ = time_block(lambda: buffer.get("Volatility 75 Index", "M5", 300), iterations=100)
    metrics.append(compute_metrics("CircularCandleBuffer (get 300 candles)", "Market Data Layer", t_ring_get))

    return metrics


def benchmark_strategy_engines(provider: MockMarketDataProvider) -> List[BenchmarkMetric]:
    """Evalúa el tiempo de cálculo de los algoritmos de trading (SMC, MSNR, ORB)."""
    metrics = []

    # 1. MultiTimeframeAnalyzer SMC (H4 -> H1 -> M15 -> M5)
    mtf_config = MultiTimeframeConfig(
        higher_timeframe="H4",
        structure_timeframe="H1",
        confirmation_timeframe="M15",
        entry_timeframe="M5",
        higher_timeframe_candles=300,
        structure_candles=300,
        confirmation_candles=300,
        entry_candles=200,
    )
    pipeline_config = PipelineConfig()
    smc_analyzer = MultiTimeframeAnalyzer(provider, mtf_config, pipeline_config)

    t_smc, _ = time_block(lambda: smc_analyzer.analyze_symbol("Volatility 75 Index"), iterations=10)
    metrics.append(compute_metrics("SMC: MultiTimeframeAnalyzer.analyze_symbol()", "Strategy Compute", t_smc))

    # 2. Malaysian SNR Strategy
    msnr_strategy = MalaysianSNRStrategy(provider)
    t_msnr, _ = time_block(lambda: msnr_strategy.analyze_symbol("Step Index"), iterations=15)
    metrics.append(compute_metrics("MSNR: analyze_symbol()", "Strategy Compute", t_msnr))

    # 3. New York ORB Strategy
    orb_config = ORBConfig()
    orb_strategy = NewYorkORBStrategy(provider, orb_config)
    t_orb, _ = time_block(lambda: orb_strategy.analyze_symbol("US Tech 100"), iterations=20)
    metrics.append(compute_metrics("ORB: analyze_symbol()", "Strategy Compute", t_orb))

    return metrics


def benchmark_memory_and_gc(provider: MockMarketDataProvider) -> Dict[str, Any]:
    """Evalúa la presión sobre el Garbage Collector y el consumo de memoria en 50 ciclos continuos."""
    tracemalloc.start()
    gc.collect()
    gc_counts_before = gc.get_count()

    # Ejecutar 50 evaluaciones consecutivas de estrategias
    mtf = MultiTimeframeAnalyzer(provider)
    msnr = MalaysianSNRStrategy(provider)
    for _ in range(50):
        _ = mtf.analyze_symbol("Volatility 75 Index")
        _ = msnr.analyze_symbol("Step Index")

    current_mem, peak_mem = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    gc_counts_after = gc.get_count()

    return {
        "current_memory_mb": current_mem / (1024 * 1024),
        "peak_memory_mb": peak_mem / (1024 * 1024),
        "gc_gen0_collections": gc_counts_after[0] - gc_counts_before[0],
        "gc_gen1_collections": gc_counts_after[1] - gc_counts_before[1],
        "gc_gen2_collections": gc_counts_after[2] - gc_counts_before[2],
    }


def run_comprehensive_benchmark():
    print("=" * 80)
    print("       BLACKDAEMONFX - BENCHMARKING Y PROFILING TÉCNICO INTEGRAL       ")
    print("=" * 80)

    target_db = os.getenv("DAEMONBLACKFX_DB_PATH") or (PROJECT_ROOT / "storage" / "trading_bot.sqlite3")
    repo = TradingRepository(target_db)
    db_path = repo.db_path
    print(f"Base de datos analizada: {db_path} ({db_path.stat().st_size / (1024*1024):.2f} MB)")
    print("Iniciando medición de microsegundos y perfilado de cuellos de botella...\n")

    provider = MockMarketDataProvider()

    all_metrics: List[BenchmarkMetric] = []

    print("[1/4] Evaluando Base de Datos y Repositorio SQLite...")
    all_metrics.extend(benchmark_sqlite_and_repository(repo))

    print("[2/4] Evaluando Capa de Datos de Mercado y Caching...")
    all_metrics.extend(benchmark_candle_data_layer(provider))

    print("[3/4] Evaluando Motores de Estrategia (SMC, MSNR, ORB)...")
    all_metrics.extend(benchmark_strategy_engines(provider))

    print("[4/4] Evaluando Memoria y Comportamiento del Garbage Collector...")
    mem_stats = benchmark_memory_and_gc(provider)

    # Imprimir Tabla de Resultados
    print("\n" + "=" * 95)
    print(f"{'OPERACIÓN / COMPONENTE':<45} | {'CATEGORÍA':<18} | {'AVG (ms)':<9} | {'P95 (ms)':<9} | {'ESTADO':<10}")
    print("=" * 95)

    bottlenecks = []
    for m in all_metrics:
        badge = "🟢 ÓPTIMO" if m.status == "OPTIMAL" else ("🟡 ACEPTABLE" if m.status == "ACCEPTABLE" else "🔴 CUELLO")
        print(f"{m.name:<45} | {m.category:<18} | {m.avg_time_ms:>8.2f} | {m.p95_time_ms:>8.2f} | {badge}")
        if m.status == "BOTTLENECK":
            bottlenecks.append(m)

    print("=" * 95)

    print("\n--- PERFILADO DE MEMORIA Y RECOLECCIÓN DE BASURA (50 CICLOS) ---")
    print(f"Memoria activa tras ciclo: {mem_stats['current_memory_mb']:.2f} MB")
    print(f"Pico de memoria en ciclo:  {mem_stats['peak_memory_mb']:.2f} MB")
    print(f"Pausas de GC (Gen0/1/2):   Gen0: {mem_stats['gc_gen0_collections']}, Gen1: {mem_stats['gc_gen1_collections']}, Gen2: {mem_stats['gc_gen2_collections']}")

    # Resumen y Recomendaciones de Ingeniería
    print("\n" + "=" * 80)
    print("                    VEREDICTO Y CUELLOS DE BOTELLA                     ")
    print("=" * 80)
    if bottlenecks:
        print(f"Se identificaron {len(bottlenecks)} puntos con latencia superior a 50 ms:")
        for b in bottlenecks:
            print(f"  • {b.name}: {b.avg_time_ms:.2f} ms (P95: {b.p95_time_ms:.2f} ms) [{b.category}]")
    else:
        print("Ningún componente superó el umbral crítico de 50 ms en ejecuciones individuales.")

    # Guardar reporte JSON en storage para trazabilidad
    report_path = PROJECT_ROOT / "storage" / "benchmark_report_latest.json"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_data = {
        "timestamp": pd.Timestamp.now(tz="UTC").isoformat(),
        "db_path": str(db_path),
        "metrics": [
            {
                "name": m.name,
                "category": m.category,
                "avg_ms": m.avg_time_ms,
                "p95_ms": m.p95_time_ms,
                "p99_ms": m.p99_time_ms,
                "status": m.status,
                "details": m.details,
            }
            for m in all_metrics
        ],
        "memory": mem_stats,
    }
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report_data, f, indent=2)
    print(f"\nReporte completo guardado en: {report_path.as_posix()}")


if __name__ == "__main__":
    run_comprehensive_benchmark()
