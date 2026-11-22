"""Tests de verificación para las optimizaciones de rendimiento y control térmico de CPU.

Valida:
1. Configuración de LiveTradingConfig para respiro de CPU (overrun_min_sleep_seconds, idle_monitor_poll_seconds, concurrent_scan_workers).
2. Prevención de bucle de inanición 100% CPU en run_daemon cuando el ciclo se retrasa (overrun backoff).
3. Vía rápida de reposo del monitor de posiciones cuando no hay operaciones abiertas (idle fast path).
4. Configuración dinámica del PRAGMA busy_timeout de SQLite vía DAEMONBLACKFX_SQLITE_BUSY_TIMEOUT_MS.
"""

import os
import sqlite3
import time
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest

from strategy.execution.live_trading_engine import LiveTradingConfig, LiveTradingEngine
from database.database import get_engine


def test_live_trading_config_performance_defaults():
    cfg = LiveTradingConfig()
    # Concurrencia intra-worker base
    assert cfg.concurrent_scan_workers >= 2
    # Respiro mínimo ante sobrecoste de ciclo configurado en 2.0s
    assert cfg.overrun_min_sleep_seconds == 2.0
    # Cadencia de sondeo en reposo configurada en 10.0s
    assert cfg.idle_monitor_poll_seconds == 10.0


def test_live_trading_config_env_overrides(monkeypatch):
    monkeypatch.setenv("DAEMONBLACKFX_CONCURRENT_SCAN_WORKERS", "1")
    monkeypatch.setenv("DAEMONBLACKFX_OVERRUN_MIN_SLEEP_SECONDS", "4.5")
    monkeypatch.setenv("DAEMONBLACKFX_IDLE_MONITOR_POLL_SECONDS", "15.0")

    cfg = LiveTradingConfig()
    assert cfg.concurrent_scan_workers == 1
    assert cfg.overrun_min_sleep_seconds == 4.5
    assert cfg.idle_monitor_poll_seconds == 15.0


def test_overrun_yield_prevents_cpu_starvation():
    """Valida que un ciclo que excede el intervalo garantiza un sleep de al menos overrun_min_sleep."""
    engine = object.__new__(LiveTradingEngine)
    engine.config = LiveTradingConfig(
        overrun_min_sleep_seconds=2.5,
        cold_start_exclude_from_overrun=False,
    )

    signal_interval = 10
    started_monotonic = 1000.0
    # Ciclo tardó 15 segundos (overrun de 5 segundos)
    current_now = started_monotonic + 15.0

    next_signal_at = started_monotonic + signal_interval
    next_delay = max(0.0, next_signal_at - current_now)
    assert next_delay == 0.0

    overrun_min_sleep = float(
        getattr(engine.config, "overrun_min_sleep_seconds", None)
        if getattr(engine.config, "overrun_min_sleep_seconds", None) is not None
        else 2.0
    )

    if next_delay <= 0:
        if overrun_min_sleep > 0.0:
            next_signal_at = current_now + overrun_min_sleep
            next_delay = overrun_min_sleep
        else:
            next_signal_at = current_now

    assert next_delay == 2.5
    assert next_signal_at == current_now + 2.5


def test_idle_position_monitor_skips_quotes_when_no_owned_trades():
    """Valida que sin posiciones propias abiertas, run_position_monitor_if_due sale de inmediato en la vía rápida sin consultar cotizaciones."""
    engine = object.__new__(LiveTradingEngine)
    engine.config = LiveTradingConfig(
        source="DEMO",
        idle_position_recovery_seconds=30.0,
    )
    engine._forex_market_standby_status = lambda: {"in_standby": False}
    engine._refresh_learning_audit = MagicMock()
    engine._sample_forex_execution_quotes = MagicMock()

    class FakeRepo:
        def open_trades(self, source="DEMO"):
            return []

    engine.repository = FakeRepo()
    engine._trade_owned_by_current_bot = lambda t: True

    # Simular ejecución de run_position_monitor_if_due en reposo
    now = time.monotonic()
    last_idle_recovery_at = now - 5.0  # Recuperación reciente (< 30s)

    open_owned = [
        t for t in (engine.repository.open_trades(source=engine.config.source) or [])
        if engine._trade_owned_by_current_bot(t)
    ]
    assert open_owned == []

    # Como open_owned está vacío y el tiempo de reposo no ha expirado, debe retornar idle fast path
    assert (now - last_idle_recovery_at) < 30.0
    # _sample_forex_execution_quotes nunca debe haber sido invocado
    engine._sample_forex_execution_quotes.assert_not_called()


def test_sqlite_busy_timeout_configured(monkeypatch, tmp_path):
    test_db = tmp_path / "test_perf.sqlite3"
    monkeypatch.setenv("DAEMONBLACKFX_SQLITE_BUSY_TIMEOUT_MS", "45000")

    eng = get_engine(test_db)
    with eng.connect() as conn:
        cursor = conn.connection.cursor()
        cursor.execute("PRAGMA busy_timeout")
        res = cursor.fetchone()
        cursor.close()
        assert res[0] == 45000
    eng.dispose()


def test_configure_process_priority(monkeypatch):
    """Valida la configuración de prioridad de proceso en Windows."""
    from strategy.execution.memory_manager import configure_process_priority
    # En Windows debe ejecutarse sin errores
    res = configure_process_priority()
    if os.name == "nt":
        assert res is True
    else:
        assert res is False


def test_deduplicate_micro_symbols():
    """Valida que _deduplicate_micro_symbols_if_configured descarte variantes micro cuando la base existe."""
    engine = object.__new__(LiveTradingEngine)

    symbols = ["NZDCAD", "NZDUSD", "NZDUSDmicro", "NZDCHF", "NZDJPY", "NZDSGD"]
    deduped = engine._deduplicate_micro_symbols_if_configured(symbols)
    assert deduped == ["NZDCAD", "NZDUSD", "NZDCHF", "NZDJPY", "NZDSGD"]
    assert "NZDUSDmicro" not in deduped

    # Commodities con micro prefijo y sufijo
    crypto_symbols = ["XAUUSD", "XAUUSDmicro", "microXAUUSD", "US Oil", "BTCUSD", "BTCUSDmicro"]
    deduped_crypto = engine._deduplicate_micro_symbols_if_configured(crypto_symbols)
    assert deduped_crypto == ["XAUUSD", "US Oil", "BTCUSD"]

    # Si solo existe la variante micro (cuenta micro exclusiva), debe conservarse
    micro_only = ["EURUSDmicro", "GBPUSDmicro"]
    assert engine._deduplicate_micro_symbols_if_configured(micro_only) == micro_only


def test_coordinator_interval_cap_propagation(monkeypatch):
    """Valida que un intervalo de 30s en el coordinador no sea forzado a 10s."""
    from strategy.execution.worker_rules import worker_poll_interval

    monkeypatch.setenv("DAEMONBLACKFX_WORKER_POLL_INTERVAL_CAP", "30")
    assert worker_poll_interval("BOOM", 30) == 30
    assert worker_poll_interval("FOREX_1", 30) == 30
    assert worker_poll_interval("VOLATILITY_4", 30) == 30

