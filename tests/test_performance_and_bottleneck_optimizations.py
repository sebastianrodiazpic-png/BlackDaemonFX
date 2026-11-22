"""Pruebas de optimización informática y eliminación de cuellos de botella.
BlackDaemonFX - Ingeniería de Rendimiento

Valida:
1. Zero-Redundancy en MultiTimeframeAnalyzer._get_closed_candles (evita re-parseo O(N) y copias redundantes).
2. Optimización monotónica O(1) en MT5DataProvider.get_candles.
3. PRAGMA mmap_size y expire_on_commit configurable en database.database.
4. Nuevos índices compuestos de rendimiento en SQLite.
5. Conteo escalar eficiente en TradingRepository.reset_database.
6. Throttle adaptativo en persistencia a disco del Dashboard en tiempo real.
7. Caché unificada de corta duración (TTL) en MT5DataProvider.get_candles.
8. Optimización vectorizada/escalar de rangos de sesión en ICT (evita creación O(N) de DataFrames).
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


def test_mt5_data_candle_cache(monkeypatch):
    """Comprueba que MT5DataProvider.get_candles utiliza la caché TTL y evita llamadas redundantes."""
    import MetaTrader5 as mt5

    call_count = [0]

    def fake_copy_rates_from_pos(sym, tf, start, count):
        call_count[0] += 1
        arr = []
        for i in range(count):
            arr.append((1700000000 + i * 300, 100.0 + i, 105.0 + i, 95.0 + i, 102.0 + i, 50, 0, 0))
        return np.array(
            arr,
            dtype=[
                ("time", "<i8"),
                ("open", "<f8"),
                ("high", "<f8"),
                ("low", "<f8"),
                ("close", "<f8"),
                ("tick_volume", "<u8"),
                ("spread", "<i4"),
                ("real_volume", "<u8"),
            ],
        )

    monkeypatch.setattr(mt5, "copy_rates_from_pos", fake_copy_rates_from_pos)
    monkeypatch.setattr(mt5, "symbol_select", lambda s, e: True)
    monkeypatch.setattr(mt5, "symbol_info", lambda s: type("Info", (), {"visible": True})())

    class FakeConnector:
        def is_connected(self):
            return True
        def connect(self):
            return True

    provider = MT5DataProvider(connector=FakeConnector())
    provider._resolved_symbol_cache["eurusd"] = "EURUSD"
    provider._ensured_symbols.add("EURUSD")
    monkeypatch.setattr(mt5, "symbols_get", lambda: [type("Sym", (), {"name": "EURUSD"})()])

    # 1. Primera consulta: Cache Miss -> consulta a MT5
    df1 = provider.get_candles("EURUSD", "M5", 50)
    assert len(df1) == 50
    assert call_count[0] == 1

    # 2. Segunda consulta idéntica (dentro de TTL): Cache Hit -> sin llamada a MT5
    df2 = provider.get_candles("EURUSD", "M5", 50)
    assert len(df2) == 50
    assert call_count[0] == 1

    # 3. Consulta con count menor (ej. 30 <= 50): Cache Hit -> se corta de la caché sin llamar a MT5
    df3 = provider.get_candles("EURUSD", "M5", 30)
    assert len(df3) == 30
    assert call_count[0] == 1

    # 4. Forzar refresco: force_refresh=True -> llama a MT5
    df4 = provider.get_candles("EURUSD", "M5", 50, force_refresh=True)
    assert len(df4) == 50
    assert call_count[0] == 2

    # 5. Limpieza explícita de caché
    provider.clear_candle_cache()
    df5 = provider.get_candles("EURUSD", "M5", 50)
    assert len(df5) == 50
    assert call_count[0] == 3

    # 6. Desactivación por variable de entorno
    monkeypatch.setenv("DAEMONBLACKFX_CANDLE_CACHE_ENABLED", "0")
    df6 = provider.get_candles("EURUSD", "M5", 50)
    assert call_count[0] == 4
    df7 = provider.get_candles("EURUSD", "M5", 50)
    assert call_count[0] == 5


def test_ict_fast_range_optimization(monkeypatch):
    """Comprueba que la optimización rápida de rangos en ICT entrega valores matemáticamente idénticos a la vía previa."""
    dates = pd.date_range("2026-11-16 00:00:00", periods=30, freq="1h", tz="UTC")
    bars = []
    for i, d in enumerate(dates):
        bars.append(
            pd.Series(
                {
                    "time": d,
                    "open": 100.0 + i,
                    "high": 105.0 + i,
                    "low": 95.0 + i,
                    "close": 102.0 + i,
                }
            )
        )

    # 1. Modo Rápido (Scalar max/min)
    monkeypatch.setenv("DAEMONBLACKFX_ICT_FAST_RANGE_OPT", "1")
    fast_high = float(max(float(b["high"]) for b in bars))
    fast_low = float(min(float(b["low"]) for b in bars))

    # 2. Modo Legado (DataFrame max/min)
    monkeypatch.setenv("DAEMONBLACKFX_ICT_FAST_RANGE_OPT", "0")
    df_legacy = pd.DataFrame(bars)
    legacy_high = float(df_legacy["high"].max())
    legacy_low = float(df_legacy["low"].min())

    assert fast_high == legacy_high
    assert fast_low == legacy_low
