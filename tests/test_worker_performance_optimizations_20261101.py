"""Tests de regresión para las optimizaciones de rendimiento de workers (01-nov-2026).

Valida:
1. Zero-Copy DataFrame passing hacia el Criterio Humano (evita re-petición a get_candles).
2. TTL Cache en settings de Malaysian SNR (evita 81 transacciones SQLAlchemy/SQLite por ciclo).
3. Estructura Cache O(1) en Malaysian SNR _setups_at_break y active_av_levels.
4. Escaneo concurrente seguro intra-worker con ThreadPoolExecutor (DAEMONBLACKFX_CONCURRENT_SCAN_WORKERS).
"""
import time
from datetime import datetime, timezone
import pandas as pd
import pytest

from strategy.execution.live_trading_engine import LiveTradingConfig, LiveTradingEngine
from strategy.malaysian_snr.config import MalaysianSNRConfig
from strategy.malaysian_snr.malaysian_snr_strategy import MalaysianSNRStrategy


class DummyProvider:
    def __init__(self):
        self.call_counts = {}

    def get_candles(self, symbol, timeframe, count=40):
        self.call_counts[timeframe] = self.call_counts.get(timeframe, 0) + 1
        times = pd.date_range("2026-01-01", periods=count, freq="15min", tz="UTC")
        return pd.DataFrame({
            "time": times, "open": 100.0, "high": 102.0, "low": 98.0, "close": 101.0, "volume": 1000.0
        })

    def get_current_tick(self, s):
        return {"bid": 100.0, "ask": 100.1, "time": datetime.now(timezone.utc)}

    def get_symbol_info(self, s):
        return {"trade_tick_size": 0.01}

    def resolve_symbol(self, s):
        return s


def test_zero_copy_human_criteria_avoids_duplicate_candles():
    engine = object.__new__(LiveTradingEngine)
    engine.config = LiveTradingConfig(bot_profile="VOLATILITY_1", human_criteria_enabled=True)
    provider = DummyProvider()
    engine.provider = provider
    from strategy.human_criteria import HumanCriteriaEngine, HumanCriteriaConfig
    engine.human_criteria_engine = HumanCriteriaEngine(HumanCriteriaConfig(enabled=True, mode="FILTER"))
    engine.repository = None

    times = pd.date_range("2026-01-01", periods=40, freq="15min", tz="UTC")
    df_fast = pd.DataFrame({"time": times, "open": 100.0, "high": 102.0, "low": 98.0, "close": 101.0, "volume": 1000.0})

    signal = {
        "direction": "BUY",
        "entry_price": 100.0,
        "stop_loss": 95.0,
        "take_profit": 110.0,
        "strategy_name": "ICT_SABRI_MALLE",
        "timeframe": "M15",
        "_cached_df_h1": df_fast,
        "_cached_df_ltf": df_fast,
    }

    decision = engine._human_criteria_entry_gate("Volatility 75 Index", "BUY", signal, None, "key")
    # Verify provider.get_candles was NOT called because _cached_df_h1 was supplied
    assert "H1" not in provider.call_counts
    assert "M15" not in provider.call_counts
    # Verify cached frames were cleaned up from signal dictionary
    assert "_cached_df_h1" not in signal
    assert "_cached_df_ltf" not in signal
    assert "human_criteria" in signal


def test_cached_msnr_runtime_settings_ttl():
    engine = object.__new__(LiveTradingEngine)
    engine.config = LiveTradingConfig(bot_profile="MALAYSIAN_SNR")
    call_tracker = {"count": 0}

    class DummyRepo:
        def latest_msnr_runtime_settings(self, source="DEMO"):
            call_tracker["count"] += 1
            return {"version": 42, "source": source}

    engine.repository = DummyRepo()

    res1 = engine._cached_msnr_runtime_settings()
    res2 = engine._cached_msnr_runtime_settings()
    res3 = engine._cached_msnr_runtime_settings()
    assert res1["version"] == 42
    assert res2["version"] == 42
    assert res3["version"] == 42
    # Only 1 DB query was made despite 3 calls
    assert call_tracker["count"] == 1


def test_concurrent_scan_workers_execution():
    engine = object.__new__(LiveTradingEngine)
    engine.config = LiveTradingConfig(bot_profile="VOLATILITY_1", concurrent_scan_workers=3)
    engine._pre_execution_ranking_enabled = lambda: False
    engine._sync_open_trades_before_execution = lambda: None
    engine.repository = None
    engine._refresh_learning_audit = lambda: None
    engine.meta_label_cycle_ranking = lambda: None
    engine._report_first_m5_cycle = lambda *a: None
    processed = []

    def mock_process_symbol(sym, sync_before_execution=False):
        processed.append(sym)
        return {"symbol": sym, "action": "WAITING_ICT", "reason": "TEST"}

    engine.process_symbol = mock_process_symbol
    engine._compact_symbol_result = lambda r: r
    engine._persist_audit_event = lambda *a, **k: None

    symbols = ["Volatility 10 Index", "Volatility 25 Index", "Volatility 50 Index", "Volatility 75 Index"]
    results = engine.process_symbols(symbols)

    assert len(results) == 4
    assert len(processed) == 4
    assert {r["symbol"] for r in results} == set(symbols)


def test_default_concurrent_scan_workers_is_at_least_two():
    cfg = LiveTradingConfig(bot_profile="VOLATILITY_1")
    assert cfg.concurrent_scan_workers >= 2


def test_ict_fast_exit_outside_killzone_skips_candle_fetching():
    from strategy.ict.ict_strategy import ICTSabriMalleStrategy, ICTSabriMalleConfig
    provider = DummyProvider()
    cfg = ICTSabriMalleConfig(killzone_filter_enabled=True, structure_timeframe="H1")
    strategy = ICTSabriMalleStrategy(provider, config=cfg)

    # Simular una hora fuera de Killzone institucional (20:00 NY = 01:00 UTC en martes)
    outside_time = pd.Timestamp("2026-10-27 01:00:00", tz="UTC")
    res = strategy.analyze_symbol("US Tech 100", now_utc=outside_time)

    assert res["valid"] is False
    assert "OUTSIDE_INSTITUTIONAL_KILLZONE" in res["reason"]
    # provider.get_candles no fue invocado
    assert "H1" not in provider.call_counts


def test_rotate_worker_log_if_needed(tmp_path):
    from app.main import _rotate_worker_log_if_needed
    test_log = tmp_path / "test_worker.log"
    with open(test_log, "w", encoding="utf-8") as f:
        for i in range(100):
            f.write(f"Line {i}: " + "X" * 100 + "\n")
    size_before = test_log.stat().st_size
    _rotate_worker_log_if_needed(test_log, max_bytes=500, keep_tail_lines=10)
    assert test_log.stat().st_size < size_before
    with open(test_log, "r", encoding="utf-8") as f:
        content = f.read()
    assert "LOG ROTATED" in content
    assert "Line 99" in content
    assert (tmp_path / "test_worker.log.old").exists()


def test_adaptive_thread_scaling_by_basket_size():
    import os
    engine = object.__new__(LiveTradingEngine)
    engine.config = LiveTradingConfig(bot_profile="MALAYSIAN_SNR", concurrent_scan_workers=2)
    engine._pre_execution_ranking_enabled = lambda: False
    engine._sync_open_trades_before_execution = lambda: None
    engine.repository = None
    engine._refresh_learning_audit = lambda: None
    engine.meta_label_cycle_ranking = lambda: None
    engine._report_first_m5_cycle = lambda *a: None
    engine._compact_symbol_result = lambda r: r
    engine._persist_audit_event = lambda *a, **k: None

    spawned_workers = []

    class MockFuture:
        def __init__(self, fn, *args):
            self._fn = fn
            self._args = args
        def result(self):
            return self._fn(*self._args)

    class MockExecutor:
        def __init__(self, max_workers=None):
            spawned_workers.append(max_workers)
        def __enter__(self):
            return self
        def __exit__(self, *args):
            pass
        def submit(self, fn, *args, **kwargs):
            return MockFuture(fn, *args)

    import concurrent.futures
    import unittest.mock as mock

    engine.process_symbol = lambda s, **k: {"symbol": s, "action": "WAITING_ICT", "reason": "TEST"}

    # Canasta de 25 símbolos: escala a 4 (o CPU count)
    basket_25 = [f"Sym_{i}" for i in range(25)]
    with mock.patch("concurrent.futures.ThreadPoolExecutor", MockExecutor):
        engine.process_symbols(basket_25)
    expected_large = min(4, os.cpu_count() or 4)
    assert spawned_workers[-1] == expected_large

    # Canasta de 12 símbolos: escala a 3
    basket_12 = [f"Sym_{i}" for i in range(12)]
    with mock.patch("concurrent.futures.ThreadPoolExecutor", MockExecutor):
        engine.process_symbols(basket_12)
    expected_med = min(3, os.cpu_count() or 3)
    assert spawned_workers[-1] == expected_med

    # Canasta de 5 símbolos: se queda en 2
    basket_5 = [f"Sym_{i}" for i in range(5)]
    with mock.patch("concurrent.futures.ThreadPoolExecutor", MockExecutor):
        engine.process_symbols(basket_5)
    assert spawned_workers[-1] == 2


def test_ict_adx_early_exit_skips_h4_and_ltf():
    from strategy.ict.ict_strategy import ICTSabriMalleStrategy, ICTSabriMalleConfig
    import numpy as np

    class AdxProvider(DummyProvider):
        def get_candles(self, symbol, timeframe, count=40):
            self.call_counts[timeframe] = self.call_counts.get(timeframe, 0) + 1
            times = pd.date_range("2026-01-01", periods=count, freq="1h", tz="UTC")
            # Serie sin tendencia lateral oscilante para forzar ADX bajo (< 10)
            prices = 100.0 + (np.arange(count) % 2) * 0.01
            return pd.DataFrame({
                "time": times, "open": prices, "high": prices + 0.02, "low": prices - 0.02, "close": prices, "volume": 1000.0
            })

    provider = AdxProvider()
    cfg = ICTSabriMalleConfig(
        killzone_filter_enabled=False,
        structure_timeframe="H1",
        macro_timeframe="H4",
        entry_timeframe="M15",
    )
    cfg.min_adx_h1 = 25.0
    strategy = ICTSabriMalleStrategy(provider, config=cfg)
    res = strategy.analyze_symbol("Volatility 75 Index", now_utc=pd.Timestamp("2026-10-27 14:00:00", tz="UTC"))

    assert res["valid"] is False
    assert "INSUFFICIENT_H1_ADX_REGIME" in res["reason"]
    # H1 debió ser consultado para calcular el ADX temprano
    assert provider.call_counts.get("H1", 0) > 0
    # Pero H4 y M15 NO debieron ser consultados en absoluto
    assert provider.call_counts.get("H4", 0) == 0
    assert provider.call_counts.get("M15", 0) == 0


def test_gc_tuning_configuration(monkeypatch):
    import gc
    from app.main import _configure_gc_tuning
    monkeypatch.setenv("DAEMONBLACKFX_GC_THRESHOLD", "88888")
    _configure_gc_tuning()
    thresh = gc.get_threshold()
    assert thresh[0] == 88888
    # Restaurar
    gc.set_threshold(70000, 10, 10)


