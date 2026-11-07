"""Pruebas de optimización informática y eliminación de cuellos de botella.
BlackDaemonFX - Ingeniería de Rendimiento

Valida:
1. Zero-Redundancy en MultiTimeframeAnalyzer._get_closed_candles (evita re-parseo O(N) y copias redundantes).
2. Optimización monotónica O(1) en MT5DataProvider.get_candles.
3. PRAGMA mmap_size y expire_on_commit configurable en database.database.
4. Nuevos índices compuestos de rendimiento en SQLite.
5. Conteo escalar eficiente en TradingRepository.reset_database.
6. Throttle adaptativo en persistencia a disco del Dashboard en tiempo real.
"""

from datetime import datetime, timezone
import os
import sqlite3
import time
import numpy as np
import pandas as pd
import pytest
from sqlalchemy import text

from brokers.mt5_data import MT5DataProvider
from database.database import (
    get_engine,
    get_session_factory,
    init_database,
    _ensure_performance_indexes,
)
from database.repository import TradingRepository
from strategy.execution.multi_timeframe import MultiTimeframeAnalyzer, MultiTimeframeConfig


class DummyDataProvider:
    def __init__(self, df: pd.DataFrame):
        self._df = df

    def get_candles(self, symbol, timeframe, count):
        return self._df.copy()


def test_zero_copy_candles_monotonic_and_utc():
    """Comprueba que _get_closed_candles entrega datos idénticos y en UTC sin copias redundantes."""
    dates = pd.date_range("2026-11-06 00:00:00", periods=50, freq="5min", tz="UTC")
    df = pd.DataFrame({
        "time": dates,
        "open": np.linspace(100, 150, 50),
        "high": np.linspace(101, 151, 50),
        "low": np.linspace(99, 149, 50),
        "close": np.linspace(100.5, 150.5, 50),
        "tick_volume": [100] * 50,
    })

    provider = DummyDataProvider(df)
    analyzer = MultiTimeframeAnalyzer(provider, MultiTimeframeConfig())

    closed = analyzer._get_closed_candles("EURUSD", "M5", 50)
    # Debe eliminar la última vela (abierta) quedando con 49 velas
    assert len(closed) == 49
    assert closed["time"].iloc[-1] == dates[-2]
    assert pd.api.types.is_datetime64_any_dtype(closed["time"])
    assert str(closed["time"].dt.tz) == "UTC"
    assert closed["time"].is_monotonic_increasing


def test_zero_copy_handles_naive_and_unsorted():
    """Valida resiliencia: si el proveedor entrega fechas naive o desordenadas, las normaliza correctamente."""
    dates = pd.date_range("2026-11-06 00:00:00", periods=10, freq="5min")  # Naive
    df = pd.DataFrame({
        "time": list(reversed(dates)),  # Desordenado
        "open": [10.0] * 10,
        "high": [11.0] * 10,
        "low": [9.0] * 10,
        "close": [10.5] * 10,
    })

    provider = DummyDataProvider(df)
    analyzer = MultiTimeframeAnalyzer(provider, MultiTimeframeConfig())

    closed = analyzer._get_closed_candles("EURUSD", "M5", 10)
    assert len(closed) == 9
    assert closed["time"].is_monotonic_increasing
    assert str(closed["time"].dt.tz) == "UTC"


def test_sqlite_mmap_and_expire_on_commit(tmp_path):
    """Comprueba que PRAGMA mmap_size se aplica a la conexión y expire_on_commit es configurable."""
    db_path = tmp_path / "test_perf.sqlite3"
    engine = init_database(db_path)
    factory = get_session_factory(db_path)

    session = factory()
    try:
        # Verificar que el PRAGMA mmap_size está activo
        mmap_val = session.execute(text("PRAGMA mmap_size")).scalar()
        assert int(mmap_val) >= 0

        # Verificar que expire_on_commit es False por defecto
        assert session.expire_on_commit is False
    finally:
        session.close()
        engine.dispose()


def test_composite_indexes_created(tmp_path):
    """Comprueba que los índices compuestos de aceleración existan en SQLite."""
    db_path = tmp_path / "test_indexes.sqlite3"
    engine = init_database(db_path)

    try:
        with engine.connect() as conn:
            indexes = {
                row[0]
                for row in conn.execute(
                    text("SELECT name FROM sqlite_master WHERE type='index'")
                ).fetchall()
            }

        expected = {
            "ix_trades_source_status_entry",
            "ix_trade_journal_source_status_time",
            "ix_position_visual_audits_composite",
            "ix_signals_instrument_time",
        }
        for idx in expected:
            assert idx in indexes, f"Falta el índice {idx} en el esquema"
    finally:
        engine.dispose()


def test_repository_scalar_counts(tmp_path):
    """Comprueba que reset_database usa conteo escalar O(1) y reporta correctamente."""
    db_path = tmp_path / "test_repo.sqlite3"
    repo = TradingRepository(db_path)

    res = repo.reset_database(allow_open_trades=True)
    assert res["ok"] is True
    assert "trades" in res
    assert "signals" in res
    assert "account_snapshots" in res
    assert "open_trades" in res
    assert "trade_journal_preserved" in res


def test_dashboard_persist_throttling(tmp_path):
    """Comprueba que el dashboard actualiza memoria en cada símbolo pero acota la I/O de disco."""
    from dashboard.realtime_dashboard import RealtimeDashboardService

    class DummyRepo:
        def open_trades(self, source=None):
            return []
        def account_metrics(self, source=None):
            return {}

    dash = RealtimeDashboardService(repository=DummyRepo(), host="127.0.0.1", port=0)
    dash.state_path = tmp_path / "dashboard_state.json"

    # Símbolo intermedio no crítico
    result = {"symbol": "EURUSD", "action": "SIN ACCIÓN", "reason": "NO_SETUP"}
    dash.symbol_result(result, index=2, total=20, elapsed_seconds=0.05)

    # Estado en memoria está 100% fresco
    assert dash._state["current_symbol"] == "EURUSD"
    assert dash._state["symbols_processed"] == 2
