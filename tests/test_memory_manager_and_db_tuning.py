"""tests/test_memory_manager_and_db_tuning.py - Validación de optimizaciones de rendimiento y memoria."""

import os
import sqlite3
import time
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from strategy.execution.memory_manager import optimize_process_memory
from strategy.execution.worker_rules import worker_poll_interval
from strategy.execution.live_trading_engine import LiveTradingConfig, LiveTradingEngine
from tools.operator.db_optimizer import (
    ensure_performance_optimizations,
    get_db_storage_stats,
    prune_ephemeral_telemetry,
    run_passive_checkpoint,
    vacuum_database,
)


def test_optimize_process_memory_execution():
    """Valida que optimize_process_memory se ejecute correctamente y retorne métricas."""
    stats = optimize_process_memory()
    assert isinstance(stats, dict)
    assert "gc_collected" in stats
    assert "trimmed_working_set" in stats
    assert isinstance(stats["gc_collected"], int)


def test_worker_poll_interval_configurable_cap(monkeypatch):
    """Valida que worker_poll_interval respete DAEMONBLACKFX_WORKER_POLL_INTERVAL_CAP."""
    # Por defecto cap = 10
    monkeypatch.delenv("DAEMONBLACKFX_WORKER_POLL_INTERVAL_CAP", raising=False)
    assert worker_poll_interval("BOOM", 30) == 10
    assert worker_poll_interval("VOLATILITY_1", 15) == 10
    assert worker_poll_interval("FOREX_1", 5) == 5

    # Con cap aumentado a 25
    monkeypatch.setenv("DAEMONBLACKFX_WORKER_POLL_INTERVAL_CAP", "25")
    assert worker_poll_interval("BOOM", 30) == 25
    assert worker_poll_interval("VOLATILITY_1", 20) == 20
    assert worker_poll_interval("FOREX_1", 10) == 10

    # Perfiles no limitados (ORB, MALAYSIAN_SNR)
    assert worker_poll_interval("ORB", 30) == 30
    assert worker_poll_interval("MALAYSIAN_SNR", 45) == 45


def test_audit_cycle_start_active_throttling(monkeypatch):
    """Valida que DAEMON_CYCLE_START se amortigüe ante ciclos repetidos con símbolos activos."""
    monkeypatch.setenv("DAEMONBLACKFX_AUDIT_CYCLE_START_THROTTLE_SECONDS", "60.0")

    engine = LiveTradingEngine.__new__(LiveTradingEngine)
    engine.config = LiveTradingConfig(bot_profile="BOOM")
    mock_repo = SimpleNamespace(
        upsert_worker_runtime_state=Mock(),
        save_audit_event=Mock(return_value=1),
    )
    engine.repository = mock_repo

    clock = [100.0]
    monkeypatch.setattr("strategy.execution.live_trading_engine.time.monotonic", lambda: clock[0])

    payload = {"symbols_count": 5, "selected_symbols_count": 5, "runtime_state": "RUNNING"}

    # 1. Primer ciclo: se guarda en la base de datos
    res1 = engine._persist_audit_event("DAEMON_CYCLE_START", payload=payload)
    assert mock_repo.save_audit_event.call_count == 1
    assert mock_repo.upsert_worker_runtime_state.call_count == 1

    # 2. Segundo ciclo a los 10 segundos (misma firma): se amortigua en DB (runtime_only)
    clock[0] = 110.0
    res2 = engine._persist_audit_event("DAEMON_CYCLE_START", payload=payload)
    assert res2.get("sampled_active_cycle") is True
    assert mock_repo.save_audit_event.call_count == 1  # No aumentó escritura
    assert mock_repo.upsert_worker_runtime_state.call_count == 2  # Heartbeat en vivo sí se actualizó

    # 3. Cambio de estado en runtime: debe guardarse de inmediato
    clock[0] = 115.0
    payload_changed = {**payload, "runtime_state": "WAITING_NEW_BAR"}
    res3 = engine._persist_audit_event("DAEMON_CYCLE_START", payload=payload_changed)
    assert mock_repo.save_audit_event.call_count == 2
    assert mock_repo.upsert_worker_runtime_state.call_count == 3

    # 4. Transcurrieron más de 60 segundos: se guarda nuevamente
    clock[0] = 180.0
    res4 = engine._persist_audit_event("DAEMON_CYCLE_START", payload=payload_changed)
    assert mock_repo.save_audit_event.call_count == 3
    assert mock_repo.upsert_worker_runtime_state.call_count == 4


def test_db_optimizer_suite_on_temporary_database(tmp_path):
    """Valida optimizaciones, checkpoint, prunings y vacuum en una base temporal."""
    test_db = tmp_path / "test_trading.sqlite3"
    conn = sqlite3.connect(str(test_db))
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE daemon_audit_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            event_type TEXT,
            action TEXT,
            event_time TIMESTAMP,
            created_at TIMESTAMP
        );
    """)
    cur.execute("CREATE TABLE trades (id INTEGER PRIMARY KEY);")

    # Insertar eventos antiguos y recientes
    for i in range(10):
        cur.execute(
            "INSERT INTO daemon_audit_events (event_type, action, event_time, created_at) VALUES ('CYCLE_START', 'CYCLE_START', datetime('now', '-5 days'), datetime('now', '-5 days'));"
        )
    for i in range(5):
        cur.execute(
            "INSERT INTO daemon_audit_events (event_type, action, event_time, created_at) VALUES ('CYCLE_START', 'CYCLE_START', datetime('now', '-1 days'), datetime('now', '-1 days'));"
        )
    conn.commit()
    conn.close()

    # 1. Stats
    stats = get_db_storage_stats(test_db)
    assert stats["table_counts"]["daemon_audit_events"] == 15

    # 2. Optimización de índices
    opt = ensure_performance_optimizations(test_db)
    assert opt["status"] == "OK"

    # 3. Purgado de telemetría efímera (>3 días)
    prune_res = prune_ephemeral_telemetry(test_db, retention_days=3)
    assert prune_res["ephemeral_events_pruned"] == 10

    # 4. Checkpoint
    chk = run_passive_checkpoint(test_db)
    assert chk["status"] == "OK"

    # 5. Vacuum
    vac = vacuum_database(test_db)
    assert vac["status"] == "OK"

    # Verificar que solo quedan los 5 eventos recientes
    stats_after = get_db_storage_stats(test_db)
    assert stats_after["table_counts"]["daemon_audit_events"] == 5
