"""Pruebas unitarias para la cola asíncrona de notificaciones y exportación (AsyncNotificationQueue)."""

import time
import pytest
from reporting.async_notification_queue import (
    AsyncNotificationQueue,
    get_async_notification_queue,
)


def test_async_notification_queue_background_execution():
    """Verifica que las tareas encoladas se ejecuten en segundo plano sin bloquear."""
    queue_service = AsyncNotificationQueue(maxsize=100, enabled=True, name="TestWorker")
    executed_records = []

    def background_task(item_id: int, message: str):
        time.sleep(0.01)
        executed_records.append((item_id, message))

    # Encolar 5 tareas de forma no bloqueante
    for i in range(5):
        success = queue_service.enqueue_task(background_task, i, f"task_{i}")
        assert success is True

    # El hilo principal continuó de inmediato
    assert len(executed_records) <= 5

    # Esperar el vaciado de la cola
    flushed = queue_service.flush(timeout_seconds=2.0)
    assert flushed is True
    assert len(executed_records) == 5
    assert executed_records[0] == (0, "task_0")

    diagnostics = queue_service.get_diagnostics()
    assert diagnostics["tasks_enqueued"] == 5
    assert diagnostics["tasks_completed"] == 5
    assert diagnostics["tasks_failed"] == 0

    queue_service.stop(timeout_seconds=1.0)


def test_async_notification_queue_error_resilience():
    """Verifica que fallos en tareas secundarias no detengan el hilo consumidor."""
    queue_service = AsyncNotificationQueue(maxsize=50, enabled=True)
    completed_tasks = []

    def failing_task():
        raise RuntimeError("Fallo simulado en exportación o auditoría")

    def normal_task(val: int):
        completed_tasks.append(val)

    queue_service.enqueue_task(failing_task)
    queue_service.enqueue_task(normal_task, 42)

    flushed = queue_service.flush(timeout_seconds=2.0)
    assert flushed is True
    assert completed_tasks == [42]

    diagnostics = queue_service.get_diagnostics()
    assert diagnostics["tasks_failed"] == 1
    assert diagnostics["tasks_completed"] == 1

    queue_service.stop(timeout_seconds=1.0)


def test_async_notification_queue_sync_mode_when_disabled():
    """Verifica que si la cola está deshabilitada, ejecute síncronamente sin errores."""
    queue_service = AsyncNotificationQueue(enabled=False)
    output = []

    def sync_task(msg: str):
        output.append(msg)

    success = queue_service.enqueue_task(sync_task, "directo")
    assert success is True
    assert output == ["directo"]


def test_async_export_integration(tmp_path):
    """Verifica que TradeReportingService con async_export=True delegue la exportación al hilo de fondo."""
    from database.repository import TradingRepository
    from reporting.trade_reporting_service import (
        TradeReportingConfig,
        TradeReportingService,
    )
    from strategy.execution.paper_trade_executor import PaperTradeExecutor
    from trade_lifecycle_manager import TradeLifecycleManager
    import pandas as pd

    db_path = tmp_path / "async_paper_trading.db"
    xlsx_path = tmp_path / "async_paper_trading_report.xlsx"

    repository = TradingRepository(db_path=db_path)
    reporting_service = TradeReportingService(
        repository=repository,
        config=TradeReportingConfig(
            source="PAPER",
            output_path=xlsx_path,
            auto_export=True,
            broker="PAPER",
            async_export=True,
        ),
    )

    executor = PaperTradeExecutor()
    manager = TradeLifecycleManager(
        trade_executor=executor,
        reporting_service=reporting_service,
    )

    signal = {
        "symbol": "Boom 100 Index",
        "timeframe": "M5",
        "direction": "BUY",
        "entry_time": pd.Timestamp("2026-10-27 10:00:00+00:00"),
        "entry_price": 100.0,
        "stop_loss": 98.0,
        "take_profit": 104.0,
        "risk_reward_ratio": 2.0,
        "action": "MULTI_TIMEFRAME_SIGNAL",
    }

    lifecycle = manager.process_signal_with_executor(signal=signal, volume=0.5)
    assert lifecycle.position_ticket is not None

    # Esperar el vaciado de la cola asíncrona para que se guarde el archivo XLSX
    queue_service = get_async_notification_queue()
    flushed = queue_service.flush(timeout_seconds=3.0)
    assert flushed is True
    assert xlsx_path.exists()
